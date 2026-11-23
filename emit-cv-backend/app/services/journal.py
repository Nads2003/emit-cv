"""Notifications in-app et journal d'historique. Les fonctions ajoutent à la session ; l'appelant fait le commit."""
from sqlalchemy.orm import Session

from app.models import Historique, Notification


def notifier(db: Session, utilisateur_id: int, message: str) -> None:
    db.add(Notification(utilisateur_id=utilisateur_id, message=message[:400]))


def journaliser(db: Session, utilisateur_id: int, action: str) -> None:
    db.add(Historique(utilisateur_id=utilisateur_id, action=action[:300]))
