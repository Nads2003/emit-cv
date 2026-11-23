"""Limitation de débit stockée EN BASE : les compteurs sont partagés entre tous les workers/serveurs (contrairement à un compteur en mémoire)."""
from datetime import timedelta

from fastapi import HTTPException, status
from sqlalchemy import delete
from sqlalchemy.orm import Session

from app.models import LimiteDebit, en_utc, utcnow


def verifier(db: Session, cle: str, limite: int, fenetre_s: int, compter: bool = True, message: str = "Trop de tentatives. Réessayez plus tard.") -> None:
    """Lève 429 si `limite` est atteinte dans la fenêtre glissante ; sinon incrémente (si `compter`)."""
    now = utcnow()
    ligne = db.get(LimiteDebit, cle, with_for_update=True)
    if ligne is None or now - en_utc(ligne.debut_fenetre) > timedelta(seconds=fenetre_s):
        if ligne is None:
            ligne = LimiteDebit(cle=cle, compteur=0, debut_fenetre=now)
            db.add(ligne)
        else:
            ligne.compteur, ligne.debut_fenetre = 0, now
    if ligne.compteur >= limite:
        db.commit()
        raise HTTPException(status.HTTP_429_TOO_MANY_REQUESTS, message, headers={"Retry-After": str(fenetre_s)})
    if compter:
        ligne.compteur += 1
    db.commit()


def reinitialiser(db: Session, cle: str) -> None:
    db.execute(delete(LimiteDebit).where(LimiteDebit.cle == cle))
    db.commit()


def tout_effacer(db: Session) -> None:  # tests
    db.execute(delete(LimiteDebit))
    db.commit()
