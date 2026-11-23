"""Tables du diagramme : Notification, Historique."""
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.user import utcnow


class Notification(Base):
    __tablename__ = "notification"
    id: Mapped[int] = mapped_column(primary_key=True)
    utilisateur_id: Mapped[int] = mapped_column(ForeignKey("utilisateur.id", ondelete="CASCADE"), index=True)  # Utilisateur 1 — 0..* Notification
    message: Mapped[str] = mapped_column("message", String(400))
    date: Mapped[datetime] = mapped_column("date", DateTime(timezone=True), default=utcnow)
    lu: Mapped[bool] = mapped_column("lu", Boolean, default=False)


class Historique(Base):
    __tablename__ = "historique"
    id: Mapped[int] = mapped_column(primary_key=True)
    utilisateur_id: Mapped[int] = mapped_column(ForeignKey("utilisateur.id", ondelete="CASCADE"), index=True)  # Utilisateur 1 — 0..* Historique
    action: Mapped[str] = mapped_column("action", String(300))
    date: Mapped[datetime] = mapped_column("date", DateTime(timezone=True), default=utcnow)
