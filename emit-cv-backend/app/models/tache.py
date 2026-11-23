"""COMPLÉMENT : file de tâches persistante (analyses de CV, calculs de classement) avec suivi d'état et reprise."""
from datetime import datetime

from sqlalchemy import JSON, DateTime, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.user import utcnow


class Tache(Base):
    """statut : en_attente | en_cours | termine | echoue. Types : analyse_cv, calcul_offre."""
    __tablename__ = "tache"
    __table_args__ = (Index("ix_tache_file", "statut", "priorite", "id"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    type: Mapped[str] = mapped_column(String(30), index=True)
    cible_id: Mapped[int] = mapped_column(Integer, index=True)  # id du CV ou de l'offre
    statut: Mapped[str] = mapped_column(String(20), default="en_attente")
    priorite: Mapped[int] = mapped_column(Integer, default=5)  # 1 = urgent
    tentatives: Mapped[int] = mapped_column(Integer, default=0)
    max_tentatives: Mapped[int] = mapped_column(Integer, default=3)
    erreur: Mapped[str] = mapped_column(Text, default="")
    resultat: Mapped[dict] = mapped_column(JSON, default=dict)
    declencheur: Mapped[str] = mapped_column(String(60), default="")
    cree_le: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    disponible_le: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)  # délai avant nouvel essai
    demarre_le: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    termine_le: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    verrouille_par: Mapped[str | None] = mapped_column(String(80), nullable=True)
    verrou_expire_le: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
