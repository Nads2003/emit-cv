"""COMPLÉMENTS : liste des étudiants autorisés, imports Excel, inscriptions en attente de vérification, compteurs anti-abus."""
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.user import utcnow


class EtudiantAutorise(Base):
    """Entrée de la liste officielle : seul un étudiant dont (email, matricule) figure ici peut créer un compte."""
    __tablename__ = "etudiant_autorise"
    id: Mapped[int] = mapped_column(primary_key=True)
    nom: Mapped[str] = mapped_column(String(120))
    prenom: Mapped[str] = mapped_column(String(120))
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)       # minuscules
    matricule: Mapped[str] = mapped_column(String(40), unique=True, index=True)    # majuscules
    import_id: Mapped[int | None] = mapped_column(ForeignKey("import_liste.id", ondelete="SET NULL"), nullable=True)
    cree_le: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    # Renseigné quand le compte est créé : une entrée ne peut servir qu'UNE fois (contrainte d'unicité)
    utilisateur_id: Mapped[int | None] = mapped_column(ForeignKey("utilisateur.id", ondelete="SET NULL"), unique=True, nullable=True)
    compte_cree_le: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class ImportListe(Base):
    """Un import Excel : d'abord un APERÇU (rien n'est appliqué), puis une confirmation explicite par l'administrateur."""
    __tablename__ = "import_liste"
    id: Mapped[int] = mapped_column(primary_key=True)
    admin_id: Mapped[int] = mapped_column(ForeignKey("administrateur.id"))
    nom_fichier: Mapped[str] = mapped_column(String(255))
    hash_fichier: Mapped[str] = mapped_column(String(64))
    statut: Mapped[str] = mapped_column(String(20), default="apercu")  # apercu | confirme | annule
    nb_lignes: Mapped[int] = mapped_column(Integer, default=0)
    nb_nouveaux: Mapped[int] = mapped_column(Integer, default=0)
    nb_maj: Mapped[int] = mapped_column(Integer, default=0)
    nb_inchanges: Mapped[int] = mapped_column(Integer, default=0)
    nb_erreurs: Mapped[int] = mapped_column(Integer, default=0)
    cree_le: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    confirme_le: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class ImportLigne(Base):
    __tablename__ = "import_ligne"
    id: Mapped[int] = mapped_column(primary_key=True)
    import_id: Mapped[int] = mapped_column(ForeignKey("import_liste.id", ondelete="CASCADE"), index=True)
    numero: Mapped[int] = mapped_column(Integer)  # numéro de ligne dans le fichier Excel
    nom: Mapped[str] = mapped_column(String(255), default="")
    prenom: Mapped[str] = mapped_column(String(255), default="")
    email: Mapped[str] = mapped_column(String(255), default="")
    matricule: Mapped[str] = mapped_column(String(255), default="")
    action: Mapped[str] = mapped_column(String(20))  # nouveau | maj | inchange | erreur
    message: Mapped[str] = mapped_column(Text, default="")


class InscriptionEnAttente(Base):
    """Inscription non encore confirmée : AUCUN compte n'existe tant que l'e-mail n'est pas vérifié."""
    __tablename__ = "inscription_en_attente"
    id: Mapped[int] = mapped_column(primary_key=True)
    autorise_id: Mapped[int] = mapped_column(ForeignKey("etudiant_autorise.id", ondelete="CASCADE"), unique=True)
    mdp_hash: Mapped[str] = mapped_column(String(255))
    mention_id: Mapped[int] = mapped_column(ForeignKey("mention.id"))
    niveau_id: Mapped[int | None] = mapped_column(ForeignKey("niveauetude.id"), nullable=True)
    token_hash: Mapped[str] = mapped_column(String(64), unique=True, index=True)  # SHA-256 : le jeton en clair n'est jamais stocké
    expire_le: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    tentatives: Mapped[int] = mapped_column(Integer, default=0)
    cree_le: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class LimiteDebit(Base):
    """Compteurs de limitation de débit stockés en base (cohérents entre plusieurs workers/serveurs)."""
    __tablename__ = "limite_debit"
    cle: Mapped[str] = mapped_column(String(200), primary_key=True)
    compteur: Mapped[int] = mapped_column(Integer, default=0)
    debut_fenetre: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
