"""Tables du diagramme : Offre, CritereOffre, Candidature, Recommandation (+ association `viser`).
COMPLÉMENTS : OffreInfos (type, dates, niveau min.) et RecommandationDetail (rang + détail explicable du score)."""
from datetime import date, datetime

from sqlalchemy import JSON, Boolean, Column, Date, DateTime, Float, ForeignKey, Integer, String, Table, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.orm.attributes import set_committed_value

from app.db.base import Base
from app.models.user import utcnow

# Association « viser » : Mention 0..* — Offre 0..*
viser = Table(
    "viser", Base.metadata,
    Column("offre_id", ForeignKey("offre.id", ondelete="CASCADE"), primary_key=True),
    Column("mention_id", ForeignKey("mention.id", ondelete="CASCADE"), primary_key=True),
)

STATUT_RECOMMANDEE = "recommandee"  # candidature générée par l'IA : l'étudiant n'a pas (encore) postulé


class OffreInfos(Base):
    """COMPLÉMENT (1—1 avec offre) : type d'opportunité, échéances, niveau d'études minimal."""
    __tablename__ = "offre_infos"
    offre_id: Mapped[int] = mapped_column(ForeignKey("offre.id", ondelete="CASCADE"), primary_key=True)
    type: Mapped[str] = mapped_column(String(20), default="stage")  # stage | emploi | projet
    date_limite: Mapped[date | None] = mapped_column(Date, nullable=True)
    periode_debut: Mapped[date | None] = mapped_column(Date, nullable=True)
    periode_fin: Mapped[date | None] = mapped_column(Date, nullable=True)
    niveauetude_min_id: Mapped[int | None] = mapped_column(ForeignKey("niveauetude.id"), nullable=True)
    niveau_obligatoire: Mapped[bool] = mapped_column(Boolean, default=False)  # True = exigence éliminatoire
    niveau_min: Mapped["NiveauEtude | None"] = relationship()  # noqa: F821


class Offre(Base):
    __tablename__ = "offre"
    id: Mapped[int] = mapped_column(primary_key=True)
    admin_id: Mapped[int] = mapped_column("administrateur_id", ForeignKey("administrateur.id"))  # Administrateur 1 — publier — 0..* Offre
    titre: Mapped[str] = mapped_column("titre", String(200))
    description: Mapped[str] = mapped_column("description", Text, default="")
    date_creation: Mapped[datetime] = mapped_column("datecreation", DateTime(timezone=True), default=utcnow)
    statut: Mapped[str] = mapped_column("statut", String(20), default="brouillon", index=True)  # brouillon | publiee | cloturee

    infos: Mapped[OffreInfos | None] = relationship(uselist=False, cascade="all, delete-orphan")
    mentions: Mapped[list["Mention"]] = relationship(secondary=viser)  # noqa: F821
    criteres: Mapped[list["CritereOffre"]] = relationship(back_populates="offre", cascade="all, delete-orphan")
    candidatures: Mapped[list["Candidature"]] = relationship(back_populates="offre", cascade="all, delete-orphan")

    def _i(self) -> OffreInfos:
        if self.infos is None:
            self.infos = OffreInfos(type="stage")
        return self.infos

    @property
    def type(self) -> str:
        return self.infos.type if self.infos else "stage"

    @type.setter
    def type(self, v: str) -> None:
        self._i().type = v

    @property
    def date_limite(self) -> date | None:
        return self.infos.date_limite if self.infos else None

    @date_limite.setter
    def date_limite(self, v) -> None:
        self._i().date_limite = v

    @property
    def periode_debut(self) -> date | None:
        return self.infos.periode_debut if self.infos else None

    @periode_debut.setter
    def periode_debut(self, v) -> None:
        self._i().periode_debut = v

    @property
    def periode_fin(self) -> date | None:
        return self.infos.periode_fin if self.infos else None

    @periode_fin.setter
    def periode_fin(self, v) -> None:
        self._i().periode_fin = v

    @property
    def niveau_min_id(self) -> int | None:
        return self.infos.niveauetude_min_id if self.infos else None

    @niveau_min_id.setter
    def niveau_min_id(self, v: int | None) -> None:
        i = self._i()
        i.niveauetude_min_id = v
        set_committed_value(i, "niveau_min", None)  # invalide le cache de la relation SANS toucher à la clé étrangère

    @property
    def niveau_obligatoire(self) -> bool:
        return bool(self.infos.niveau_obligatoire) if self.infos else False

    @niveau_obligatoire.setter
    def niveau_obligatoire(self, v: bool) -> None:
        self._i().niveau_obligatoire = v

    @property
    def niveau_min(self):
        return self.infos.niveau_min if self.infos else None

    @property
    def est_ouverte(self) -> bool:
        return self.statut == "publiee" and (self.date_limite is None or self.date_limite >= date.today())


class CritereOffre(Base):
    __tablename__ = "critereoffre"
    id: Mapped[int] = mapped_column(primary_key=True)
    offre_id: Mapped[int] = mapped_column(ForeignKey("offre.id", ondelete="CASCADE"), index=True)  # Offre 1 — 0..* CritereOffre
    competence_id: Mapped[int] = mapped_column(ForeignKey("competence.id"))  # « référence » : CritereOffre → Competence
    poids: Mapped[float] = mapped_column("poids", Float, default=1.0)  # importance relative (1 à 5)
    niveau_requis: Mapped[str] = mapped_column("niveaurequis", String(20), default="intermediaire")  # niveau de maîtrise minimal
    obligatoire: Mapped[bool] = mapped_column("obligatoire", Boolean, default=False)
    offre: Mapped[Offre] = relationship(back_populates="criteres")
    competence_ref: Mapped["Competence"] = relationship()  # noqa: F821

    @property
    def competence(self) -> str:
        return self.competence_ref.nom


class Candidature(Base):
    """Lie une offre à un CV (donc à un étudiant). statut : recommandee (générée par l'IA) | postule | valide | selectionne | refuse."""
    __tablename__ = "candidature"
    __table_args__ = (UniqueConstraint("offre_id", "cv_id", name="uq_candidature_offre_cv"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    offre_id: Mapped[int] = mapped_column(ForeignKey("offre.id", ondelete="CASCADE"), index=True)  # Offre 1 — définir — 0..* Candidature
    cv_id: Mapped[int] = mapped_column(ForeignKey("cv.id"), index=True)  # CV 1 — utilisé par — Candidature
    date: Mapped[datetime] = mapped_column("date", DateTime(timezone=True), default=utcnow)
    statut: Mapped[str] = mapped_column("statut", String(20), default=STATUT_RECOMMANDEE)

    offre: Mapped[Offre] = relationship(back_populates="candidatures")
    cv: Mapped["CV"] = relationship()  # noqa: F821
    recommandation: Mapped["Recommandation | None"] = relationship(back_populates="candidature", uselist=False, cascade="all, delete-orphan")

    @property
    def etudiant_id(self) -> int:
        return self.cv.etudiant_id

    @property
    def etudiant(self):
        return self.cv.etudiant

    @property
    def a_postule(self) -> bool:
        return self.statut != STATUT_RECOMMANDEE


class ScoringRun(Base):
    """COMPLÉMENT (audit) : trace de chaque classement — critères de l'offre, pondérations et version de l'algorithme utilisés."""
    __tablename__ = "scoring_run"
    id: Mapped[int] = mapped_column(primary_key=True)
    offre_id: Mapped[int] = mapped_column(ForeignKey("offre.id", ondelete="CASCADE"), index=True)
    version_algorithme: Mapped[str] = mapped_column(String(20))
    poids: Mapped[dict] = mapped_column(JSON, default=dict)
    criteres_offre: Mapped[dict] = mapped_column(JSON, default=dict)  # instantané des critères/exigences de l'offre
    moteur_ia: Mapped[str] = mapped_column(String(30), default="")
    statut: Mapped[str] = mapped_column(String(20), default="en_cours")  # en_cours | termine | echoue
    nb_candidats: Mapped[int] = mapped_column(Integer, default=0)
    duree_ms: Mapped[int] = mapped_column(Integer, default=0)
    erreur: Mapped[str] = mapped_column(Text, default="")
    declencheur: Mapped[str] = mapped_column(String(60), default="")
    cree_le: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class RecommandationDetail(Base):
    """COMPLÉMENT (1—1 avec recommandation) : rang dans l'offre, détail explicable du score, statut éliminatoire, run d'origine."""
    __tablename__ = "recommandation_detail"
    recommandation_id: Mapped[int] = mapped_column(ForeignKey("recommandation.id", ondelete="CASCADE"), primary_key=True)
    rang: Mapped[int] = mapped_column(Integer, default=0, index=True)
    elimine: Mapped[bool] = mapped_column(Boolean, default=False, index=True)  # exigence obligatoire de l'offre non respectée
    run_id: Mapped[int | None] = mapped_column(ForeignKey("scoring_run.id", ondelete="SET NULL"), nullable=True)
    detail: Mapped[dict] = mapped_column(JSON, default=dict)


class Recommandation(Base):
    __tablename__ = "recommandation"
    id: Mapped[int] = mapped_column(primary_key=True)
    candidature_id: Mapped[int] = mapped_column(ForeignKey("candidature.id", ondelete="CASCADE"), unique=True)  # Candidature 1 — avoir — 0..* Recommandation
    score: Mapped[int] = mapped_column("scrore", Integer, index=True)  # colonne `scrore` (sic) du diagramme, 0-100
    statut: Mapped[str] = mapped_column("statut", String(20), default="proposee")
    date: Mapped[datetime] = mapped_column("date", DateTime(timezone=True), default=utcnow)

    candidature: Mapped[Candidature] = relationship(back_populates="recommandation")
    info: Mapped[RecommandationDetail | None] = relationship(uselist=False, cascade="all, delete-orphan")

    def _i(self) -> RecommandationDetail:
        if self.info is None:
            self.info = RecommandationDetail(rang=0, detail={})
        return self.info

    @property
    def rang(self) -> int:
        return self.info.rang if self.info else 0

    @rang.setter
    def rang(self, v: int) -> None:
        self._i().rang = v

    @property
    def elimine(self) -> bool:
        return bool(self.info.elimine) if self.info else False

    @property
    def detail(self) -> dict:
        return self.info.detail if self.info else {}

    @detail.setter
    def detail(self, v: dict) -> None:
        self._i().detail = v
