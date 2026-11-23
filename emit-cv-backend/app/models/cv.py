"""Tables du diagramme : CV, ModelCV, Competence, Formation, Experience. COMPLÉMENT : CVInfos (résumé, texte extrait…)."""
from datetime import date, datetime

from sqlalchemy import JSON, Boolean, Date, DateTime, ForeignKey, Index, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.user import utcnow

NIVEAUX_MAITRISE = {"debutant": 1, "intermediaire": 2, "avance": 3, "expert": 4}


def mois_entre(debut: date | None, fin: date | None) -> int:
    if not debut:
        return 0
    fin = fin or date.today()
    return max(0, (fin.year - debut.year) * 12 + (fin.month - debut.month))


def formater_duree(debut: date | None, fin: date | None) -> str:
    """Texte de la colonne `dure` (ex. « 1 an 2 mois »)."""
    m = mois_entre(debut, fin)
    ans, mois = divmod(m, 12)
    parts = ([f"{ans} an{'s' if ans > 1 else ''}"] if ans else []) + ([f"{mois} mois"] if mois else [])
    return " ".join(parts) or "moins d'un mois"


class ModelCV(Base):
    __tablename__ = "modelcv"
    id: Mapped[int] = mapped_column(primary_key=True)
    nom: Mapped[str] = mapped_column("nom", String(80))
    description: Mapped[str] = mapped_column("description", String(255), default="")
    apercu: Mapped[str] = mapped_column("apercu", String(20), default="classique")  # clé de style (classique|moderne|academique)


class CVInfos(Base):
    """COMPLÉMENT (1—1 avec cv) : champs utiles à l'import et à l'analyse IA, absents du diagramme."""
    __tablename__ = "cv_infos"
    cv_id: Mapped[int] = mapped_column(ForeignKey("cv.id", ondelete="CASCADE"), primary_key=True)
    resume: Mapped[str] = mapped_column(Text, default="")
    texte_extrait: Mapped[str] = mapped_column(Text, default="")  # texte brut du fichier importé (analyse IA)
    fichier_nom_origine: Mapped[str | None] = mapped_column(String(255), nullable=True)
    date_maj: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class CV(Base):
    __tablename__ = "cv"
    id: Mapped[int] = mapped_column(primary_key=True)
    etudiant_id: Mapped[int] = mapped_column(ForeignKey("etudiant.id", ondelete="CASCADE"), index=True)  # Etudiant 1 — créer — 1..* CV
    model_cv_id: Mapped[int] = mapped_column("modelcv_id", ForeignKey("modelcv.id"))  # ModelCV 1 — choisi par — 0..* CV
    titre: Mapped[str] = mapped_column("titre", String(160))
    date_creation: Mapped[datetime] = mapped_column("datecreation", DateTime(timezone=True), default=utcnow)
    statut: Mapped[str] = mapped_column("statut", String(20), default="brouillon", index=True)  # brouillon | publie
    source: Mapped[str] = mapped_column("source", String(20), default="en_ligne")  # en_ligne | importe
    fichier_pdf: Mapped[str | None] = mapped_column("fichierpdf", String(255), nullable=True)  # nom du fichier importé
    est_public: Mapped[bool] = mapped_column("estpublic", Boolean, default=False)  # visible des administrateurs (= publié)

    infos: Mapped[CVInfos | None] = relationship(uselist=False, cascade="all, delete-orphan")
    analyse: Mapped["CVAnalyse | None"] = relationship(uselist=False, cascade="all, delete-orphan")
    projets: Mapped[list["Projet"]] = relationship(back_populates="cv", cascade="all, delete-orphan")
    etudiant: Mapped["Etudiant"] = relationship(back_populates="cvs")  # noqa: F821
    model_cv: Mapped[ModelCV | None] = relationship()
    competences: Mapped[list["Competence"]] = relationship(back_populates="cv", cascade="all, delete-orphan")
    formations: Mapped[list["Formation"]] = relationship(back_populates="cv", cascade="all, delete-orphan")
    experiences: Mapped[list["Experience"]] = relationship(back_populates="cv", cascade="all, delete-orphan")

    def _i(self) -> CVInfos:
        if self.infos is None:
            self.infos = CVInfos(resume="", texte_extrait="", date_maj=utcnow())
        return self.infos

    @property
    def resume(self) -> str:
        return (self.infos.resume if self.infos else "") or ""

    @resume.setter
    def resume(self, v: str) -> None:
        self._i().resume = v

    @property
    def texte_extrait(self) -> str:
        return (self.infos.texte_extrait if self.infos else "") or ""

    @texte_extrait.setter
    def texte_extrait(self, v: str) -> None:
        self._i().texte_extrait = v

    @property
    def fichier_nom_origine(self) -> str | None:
        return self.infos.fichier_nom_origine if self.infos else None

    @fichier_nom_origine.setter
    def fichier_nom_origine(self, v: str | None) -> None:
        self._i().fichier_nom_origine = v

    @property
    def date_maj(self) -> datetime:
        return (self.infos.date_maj if self.infos else None) or self.date_creation or utcnow()

    @date_maj.setter
    def date_maj(self, v: datetime) -> None:
        self._i().date_maj = v

    def calculer_completude(self) -> int:
        """Pourcentage de complétude du CV (0-100)."""
        points = [
            bool(self.titre),
            len(self.resume.strip()) >= 30,
            len(self.competences) >= 3,
            len(self.formations) >= 1,
            len(self.experiences) >= 1,
            self.model_cv_id is not None,
        ]
        return round(100 * sum(points) / len(points))


class CVAnalyse(Base):
    """COMPLÉMENT : résultat (mis en cache) de l'analyse d'un CV. Réutilisé tant que `hash_contenu` et la version n'ont pas changé.
    statut : en_attente | en_cours | ok | ocr_requis (PDF scanné) | vide | echec."""
    __tablename__ = "cv_analyse"
    cv_id: Mapped[int] = mapped_column(ForeignKey("cv.id", ondelete="CASCADE"), primary_key=True)
    statut: Mapped[str] = mapped_column(String(20), default="en_attente", index=True)
    message: Mapped[str] = mapped_column(Text, default="")
    version_extracteur: Mapped[str] = mapped_column(String(20), default="")
    hash_contenu: Mapped[str] = mapped_column(String(64), default="")
    texte_scoring: Mapped[str] = mapped_column(Text, default="")
    caracteristiques: Mapped[dict] = mapped_column(JSON, default=dict)
    analysee_le: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class Projet(Base):
    """COMPLÉMENT : projets académiques ou personnels (exigés par l'analyse « Expérience et projets »)."""
    __tablename__ = "projet"
    id: Mapped[int] = mapped_column(primary_key=True)
    cv_id: Mapped[int] = mapped_column(ForeignKey("cv.id", ondelete="CASCADE"), index=True)
    titre: Mapped[str] = mapped_column(String(160))
    description: Mapped[str] = mapped_column(Text, default="")
    type: Mapped[str] = mapped_column(String(20), default="academique")  # academique | personnel
    annee: Mapped[int | None] = mapped_column(Integer, nullable=True)
    cv: Mapped[CV] = relationship(back_populates="projets")


class Competence(Base):
    """Compétence d'un CV (composition). Si cv_id est NULL : entrée du catalogue référencée par un CritereOffre."""
    __tablename__ = "competence"
    id: Mapped[int] = mapped_column(primary_key=True)
    cv_id: Mapped[int | None] = mapped_column(ForeignKey("cv.id", ondelete="CASCADE"), index=True, nullable=True)
    nom: Mapped[str] = mapped_column("nom", String(80))
    niveau_maitrise: Mapped[str | None] = mapped_column("niveaumaitrise", String(20), default="intermediaire", nullable=True)
    cv: Mapped[CV | None] = relationship(back_populates="competences")
    __table_args__ = (Index("ix_competence_nom_lower", func.lower(nom)),)  # recherche de profils par compétence sans balayer la table


class Formation(Base):
    __tablename__ = "formation"
    id: Mapped[int] = mapped_column(primary_key=True)
    cv_id: Mapped[int] = mapped_column(ForeignKey("cv.id", ondelete="CASCADE"), index=True)
    diplome: Mapped[str] = mapped_column("diplome", String(160))
    etablissement: Mapped[str] = mapped_column("etablissement", String(160), default="")
    annee: Mapped[int | None] = mapped_column("annee", Integer, nullable=True)
    cv: Mapped[CV] = relationship(back_populates="formations")


class ExperienceInfos(Base):
    """COMPLÉMENT (1—1 avec experience) : missions et réalisations, nécessaires au critère « Adéquation aux missions »."""
    __tablename__ = "experience_infos"
    experience_id: Mapped[int] = mapped_column(ForeignKey("experience.id", ondelete="CASCADE"), primary_key=True)
    description: Mapped[str] = mapped_column(Text, default="")


class Experience(Base):
    __tablename__ = "experience"
    id: Mapped[int] = mapped_column(primary_key=True)
    cv_id: Mapped[int] = mapped_column(ForeignKey("cv.id", ondelete="CASCADE"), index=True)
    poste: Mapped[str] = mapped_column("poste", String(160))
    entreprise: Mapped[str] = mapped_column("entreprise", String(160), default="")
    dure: Mapped[str] = mapped_column("dure", String(50), default="")  # texte calculé à partir des dates (« 6 mois »)
    date_debut: Mapped[date | None] = mapped_column("datedebut", Date, nullable=True)
    date_fin: Mapped[date | None] = mapped_column("datefin", Date, nullable=True)  # NULL = en cours
    cv: Mapped[CV] = relationship(back_populates="experiences")
    infos: Mapped["ExperienceInfos | None"] = relationship(uselist=False, cascade="all, delete-orphan")

    @property
    def description(self) -> str:
        return (self.infos.description if self.infos else "") or ""

    @description.setter
    def description(self, v: str) -> None:
        if self.infos is None:
            self.infos = ExperienceInfos(description=v)
        else:
            self.infos.description = v

    def calculer_duree_mois(self) -> int:
        return mois_entre(self.date_debut, self.date_fin)
