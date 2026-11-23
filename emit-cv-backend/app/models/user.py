"""Tables du diagramme de classes : Utilisateur, Etudiant, Administrateur, Profile, Mention, NiveauEtude.
Tables COMPLÉMENTAIRES (exigences du texte du cahier des charges, absentes du diagramme) : Disponibilite, EtudiantNiveau.
Les noms de tables/colonnes du diagramme sont conservés ; les attributs Python gardent des noms snake_case."""
from datetime import date, datetime, timezone

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.orm.attributes import set_committed_value

from app.db.base import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def en_utc(dt: datetime | None) -> datetime | None:
    """SQLite renvoie des dates naïves : on les considère en UTC pour pouvoir les comparer."""
    if dt is not None and dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt


RANGS_NIVEAU = {"L1": 1, "L2": 2, "L3": 3, "M1": 4, "M2": 5}  # sert à comparer deux niveaux d'études


class Mention(Base):
    __tablename__ = "mention"
    id: Mapped[int] = mapped_column(primary_key=True)
    nom: Mapped[str] = mapped_column("nom", String(120), unique=True)
    niveaux: Mapped[list["NiveauEtude"]] = relationship(back_populates="mention", order_by="NiveauEtude.id")


class NiveauEtude(Base):
    __tablename__ = "niveauetude"
    id: Mapped[int] = mapped_column(primary_key=True)
    nom: Mapped[str] = mapped_column("nom", String(20))
    mention_id: Mapped[int] = mapped_column(ForeignKey("mention.id", ondelete="CASCADE"))  # Mention 1 — 1..* NiveauEtude
    mention: Mapped[Mention] = relationship(back_populates="niveaux")

    @property
    def rang(self) -> int:
        return RANGS_NIVEAU.get(self.nom.upper(), 0)


class Utilisateur(Base):
    __tablename__ = "utilisateur"
    id: Mapped[int] = mapped_column(primary_key=True)
    nom: Mapped[str] = mapped_column("nom", String(120))
    email: Mapped[str] = mapped_column("email", String(255), unique=True, index=True)
    mot_de_passe_hash: Mapped[str] = mapped_column("mdp", String(255))  # colonne `mdp` du diagramme : contient le HASH Argon2
    role: Mapped[str] = mapped_column("role", String(20), index=True)  # 'etudiant' | 'admin'

    __mapper_args__ = {"polymorphic_on": "role", "polymorphic_identity": "utilisateur"}


class Administrateur(Utilisateur):
    __tablename__ = "administrateur"
    id: Mapped[int] = mapped_column(ForeignKey("utilisateur.id", ondelete="CASCADE"), primary_key=True)
    poste: Mapped[str] = mapped_column("poste", String(120), default="Administrateur EMIT")
    __mapper_args__ = {"polymorphic_identity": "admin"}


class Profile(Base):
    __tablename__ = "profile"
    id: Mapped[int] = mapped_column(primary_key=True)
    etudiant_id: Mapped[int] = mapped_column(ForeignKey("etudiant.id", ondelete="CASCADE"), unique=True)  # Etudiant 1 — 1 Profile
    photo: Mapped[str | None] = mapped_column("photo", String(255), nullable=True)
    telephone: Mapped[str | None] = mapped_column("telephone", String(30), nullable=True)
    adresse: Mapped[str | None] = mapped_column("adresse", String(255), nullable=True)
    etudiant: Mapped["Etudiant"] = relationship(back_populates="profil")


class Disponibilite(Base):
    """COMPLÉMENT : « Ajouter sa disponibilité » (cahier des charges, section 4). Une ligne par étudiant."""
    __tablename__ = "disponibilite"
    id: Mapped[int] = mapped_column(primary_key=True)
    etudiant_id: Mapped[int] = mapped_column(ForeignKey("etudiant.id", ondelete="CASCADE"), unique=True)
    disponible: Mapped[bool] = mapped_column(Boolean, default=True)
    datedebut: Mapped[date | None] = mapped_column(Date, nullable=True)
    datefin: Mapped[date | None] = mapped_column(Date, nullable=True)
    type: Mapped[str] = mapped_column(String(20), default="tous")  # stage | emploi | projet | tous


class EtudiantNiveau(Base):
    """COMPLÉMENT : niveau d'études de l'étudiant (le diagramme relie NiveauEtude à Mention, pas à Etudiant)."""
    __tablename__ = "etudiant_niveau"
    etudiant_id: Mapped[int] = mapped_column(ForeignKey("etudiant.id", ondelete="CASCADE"), primary_key=True)
    niveauetude_id: Mapped[int] = mapped_column(ForeignKey("niveauetude.id"))
    niveau: Mapped[NiveauEtude] = relationship()


class Etudiant(Utilisateur):
    __tablename__ = "etudiant"
    id: Mapped[int] = mapped_column(ForeignKey("utilisateur.id", ondelete="CASCADE"), primary_key=True)
    matricule: Mapped[str] = mapped_column("matricule", String(40), unique=True, index=True)
    mention_id: Mapped[int] = mapped_column(ForeignKey("mention.id"))  # Mention 1 — regrouper — 1..* Etudiant

    mention: Mapped[Mention] = relationship()
    profil: Mapped[Profile | None] = relationship(back_populates="etudiant", uselist=False, cascade="all, delete-orphan")
    cvs: Mapped[list["CV"]] = relationship(back_populates="etudiant", cascade="all, delete-orphan")  # noqa: F821
    dispo: Mapped[Disponibilite | None] = relationship(uselist=False, cascade="all, delete-orphan")
    niveau_info: Mapped[EtudiantNiveau | None] = relationship(uselist=False, cascade="all, delete-orphan")
    __mapper_args__ = {"polymorphic_identity": "etudiant"}

    # --- accès pratiques aux tables complémentaires (le reste du code ne voit que ces attributs) ---
    def _d(self) -> Disponibilite:
        if self.dispo is None:
            self.dispo = Disponibilite(disponible=True, type="tous")
        return self.dispo

    @property
    def disponible(self) -> bool:
        return self.dispo.disponible if self.dispo else True

    @disponible.setter
    def disponible(self, v: bool) -> None:
        self._d().disponible = v

    @property
    def dispo_debut(self) -> date | None:
        return self.dispo.datedebut if self.dispo else None

    @dispo_debut.setter
    def dispo_debut(self, v) -> None:
        self._d().datedebut = v

    @property
    def dispo_fin(self) -> date | None:
        return self.dispo.datefin if self.dispo else None

    @dispo_fin.setter
    def dispo_fin(self, v) -> None:
        self._d().datefin = v

    @property
    def dispo_type(self) -> str:
        return self.dispo.type if self.dispo else "tous"

    @dispo_type.setter
    def dispo_type(self, v: str) -> None:
        self._d().type = v

    @property
    def niveau_id(self) -> int | None:
        return self.niveau_info.niveauetude_id if self.niveau_info else None

    @niveau_id.setter
    def niveau_id(self, v: int | None) -> None:
        if v is None:
            self.niveau_info = None
        elif self.niveau_info is None:
            self.niveau_info = EtudiantNiveau(niveauetude_id=v)
        else:
            self.niveau_info.niveauetude_id = v
            set_committed_value(self.niveau_info, "niveau", None)  # invalide le cache de la relation SANS toucher à la clé étrangère

    @property
    def niveau(self) -> NiveauEtude | None:
        return self.niveau_info.niveau if self.niveau_info else None
