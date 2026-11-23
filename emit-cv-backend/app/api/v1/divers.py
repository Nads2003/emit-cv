"""Notifications et référentiels (mentions, niveaux, modèles de CV, compétences)."""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.ai.skills_taxonomy import all_skill_names
from app.core.deps import get_current_user
from app.db.session import get_db
from app.models import Mention, ModelCV, Notification, Utilisateur
from app.schemas.cv import ModelCVOut

notifications = APIRouter(prefix="/notifications", tags=["Notifications"])
referentiels = APIRouter(prefix="/referentiels", tags=["Référentiels"])


class NotificationOut(BaseModel):
    model_config = {"from_attributes": True}
    id: int
    message: str
    date: object
    lu: bool


@notifications.get("", summary="Mes notifications")
def lister(user: Utilisateur = Depends(get_current_user), db: Session = Depends(get_db)):
    rows = db.scalars(select(Notification).where(Notification.utilisateur_id == user.id).order_by(Notification.date.desc()).limit(50)).all()
    non_lues = db.scalar(select(func.count()).select_from(Notification).where(Notification.utilisateur_id == user.id, Notification.lu.is_(False))) or 0
    return {"non_lues": non_lues, "items": [NotificationOut.model_validate(n) for n in rows]}


@notifications.patch("/{notif_id}/lu", status_code=204, summary="Marquer comme lue")
def marquer_lue(notif_id: int, user: Utilisateur = Depends(get_current_user), db: Session = Depends(get_db)):
    n = db.get(Notification, notif_id)
    if n is None or n.utilisateur_id != user.id:
        raise HTTPException(404, "Notification introuvable.")
    n.lu = True
    db.commit()


@notifications.post("/tout-lire", status_code=204, summary="Tout marquer comme lu")
def tout_lire(user: Utilisateur = Depends(get_current_user), db: Session = Depends(get_db)):
    for n in db.scalars(select(Notification).where(Notification.utilisateur_id == user.id, Notification.lu.is_(False))):
        n.lu = True
    db.commit()


@referentiels.get("/mentions", summary="Mentions et leurs niveaux (public : nécessaire à l'inscription)")
def mentions(db: Session = Depends(get_db)):
    rows = db.scalars(select(Mention).options(selectinload(Mention.niveaux)).order_by(Mention.nom)).all()
    return [{"id": m.id, "nom": m.nom, "niveaux": [{"id": n.id, "nom": n.nom, "rang": n.rang} for n in m.niveaux]} for m in rows]


@referentiels.get("/modeles-cv", response_model=list[ModelCVOut], summary="Modèles de CV")
def modeles(db: Session = Depends(get_db)):
    return db.scalars(select(ModelCV).order_by(ModelCV.id)).all()


@referentiels.get("/competences", response_model=list[str], summary="Compétences connues (autocomplétion)")
def competences():
    return all_skill_names()
