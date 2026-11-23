"""File de tâches persistante (PostgreSQL) : suivi d'état, essais multiples avec délai croissant, reprise, verrous anti-doublon.

Modes (TACHES_MODE) :
  inline : le serveur web traite la file juste après la réponse (développement, petits déploiements) ;
  worker : des processus dédiés (`python -m app.worker`, plusieurs possibles) traitent la file — mode recommandé en production.
Les workers se partagent la file sans conflit grâce à `SELECT … FOR UPDATE SKIP LOCKED`."""
import logging
import os
import socket
from datetime import timedelta

from sqlalchemy import func, select, update
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.session import SessionLocal
from app.models import Tache, en_utc, utcnow

log = logging.getLogger("emit.taches")
WORKER_ID = f"{socket.gethostname()}-{os.getpid()}"
BACKOFF_BASE_S = 30  # essai n : délai = BACKOFF_BASE_S × 2^(n-1)


def enqueue(db: Session, type_: str, cible_id: int, declencheur: str = "", priorite: int = 5) -> Tache:
    """Ajoute une tâche, sauf s'il en existe déjà une EN ATTENTE pour la même cible (coalescence : 100 modifications = 1 calcul)."""
    existante = db.scalar(select(Tache).where(Tache.type == type_, Tache.cible_id == cible_id, Tache.statut == "en_attente"))
    if existante:
        existante.priorite = min(existante.priorite, priorite)
        db.commit()
        return existante
    t = Tache(type=type_, cible_id=cible_id, declencheur=declencheur, priorite=priorite, max_tentatives=settings.tache_max_tentatives)
    db.add(t)
    db.commit()
    return t


def enqueue_recalcul_offres_ouvertes(db: Session, declencheur: str) -> int:
    from app.services.recommandation import offres_ouvertes
    n = 0
    for o in offres_ouvertes(db):
        enqueue(db, "calcul_offre", o.id, declencheur, priorite=6)
        n += 1
    return n


def recuperer_bloquees(db: Session) -> int:
    """Tâches « en cours » dont le verrou a expiré (worker tombé) : remises en file."""
    res = db.execute(update(Tache).where(Tache.statut == "en_cours", Tache.verrou_expire_le < utcnow())
                     .values(statut="en_attente", verrouille_par=None, erreur="Reprise après interruption du worker"))
    db.commit()
    return res.rowcount or 0


def reserver(db: Session, worker_id: str, n: int) -> list[int]:
    stmt = (select(Tache).where(Tache.statut == "en_attente", Tache.disponible_le <= utcnow())
            .order_by(Tache.priorite, Tache.id).limit(n).with_for_update(skip_locked=True))
    ids = []
    for t in db.scalars(stmt):
        t.statut, t.verrouille_par, t.demarre_le = "en_cours", worker_id, utcnow()
        t.verrou_expire_le = utcnow() + timedelta(seconds=settings.worker_verrou_s)
        ids.append(t.id)
    db.commit()
    return ids


def _handler(type_: str):
    from app.services import analyse as analyse_service, recommandation as reco_service

    def h_analyse(db, t):
        r = analyse_service.analyser_cv(db, t.cible_id)
        if r["change"]:  # le contenu a changé : les classements doivent être recalculés (une seule tâche par offre)
            from app.models import CV
            cv = db.get(CV, t.cible_id)
            if cv and cv.statut == "publie":
                enqueue_recalcul_offres_ouvertes(db, f"cv:{t.cible_id}")
        return r

    def h_calcul(db, t):
        return reco_service.recompute_offer(db, t.cible_id, declencheur=t.declencheur, notify_new=t.declencheur.startswith("publication"))

    return {"analyse_cv": h_analyse, "calcul_offre": h_calcul}[type_]


def executer(tache_id: int) -> str:
    """Exécute une tâche réservée dans sa propre session. Retourne le statut final."""
    with SessionLocal() as db:
        t = db.get(Tache, tache_id)
        try:
            resultat = _handler(t.type)(db, t)
            t = db.get(Tache, tache_id)
            t.statut, t.resultat, t.erreur, t.termine_le, t.verrouille_par = "termine", resultat or {}, "", utcnow(), None
        except Exception as exc:
            db.rollback()
            log.exception("Tâche %s (%s #%s) en erreur", tache_id, t.type if t else "?", t.cible_id if t else "?")
            t = db.get(Tache, tache_id)
            t.tentatives += 1
            t.erreur = f"{type(exc).__name__}: {exc}"[:2000]
            t.verrouille_par = None
            if t.tentatives >= t.max_tentatives:
                t.statut, t.termine_le = "echoue", utcnow()
            else:
                t.statut = "en_attente"
                t.disponible_le = utcnow() + timedelta(seconds=BACKOFF_BASE_S * 2 ** (t.tentatives - 1))
        db.commit()
        return t.statut


def traiter_lot(n: int | None = None, worker_id: str = WORKER_ID) -> int:
    """Réserve puis exécute jusqu'à n tâches. Retourne le nombre de tâches exécutées."""
    with SessionLocal() as db:
        recuperer_bloquees(db)
        ids = reserver(db, worker_id, n or settings.worker_batch)
    for i in ids:
        executer(i)
    return len(ids)


def vider_la_file(max_taches: int = 500) -> int:
    """Mode inline / tests : traite la file jusqu'à ce qu'il n'y ait plus rien de disponible."""
    total = 0
    while total < max_taches:
        n = traiter_lot(50)
        if n == 0:
            break
        total += n
    return total


def declencher_inline() -> None:
    """À appeler en tâche de fond après une réponse : ne fait quelque chose qu'en mode « inline »."""
    if settings.taches_mode == "inline":
        try:
            vider_la_file()
        except Exception:
            log.exception("Traitement inline de la file en erreur")


def relancer(db: Session, tache_id: int) -> bool:
    t = db.get(Tache, tache_id)
    if t is None or t.statut != "echoue":
        return False
    t.statut, t.tentatives, t.erreur, t.disponible_le, t.termine_le = "en_attente", 0, "", utcnow(), None
    db.commit()
    return True


def relancer_echouees(db: Session) -> int:
    """Remet en file UNIQUEMENT les tâches échouées (les autres ne sont pas retraitées)."""
    res = db.execute(update(Tache).where(Tache.statut == "echoue").values(statut="en_attente", tentatives=0, erreur="", disponible_le=utcnow(), termine_le=None))
    db.commit()
    return res.rowcount or 0


def resume(db: Session) -> dict:
    lignes = db.execute(select(Tache.type, Tache.statut, func.count()).group_by(Tache.type, Tache.statut)).all()
    out: dict = {}
    for t, s, n in lignes:
        out.setdefault(t, {})[s] = n
    return out
