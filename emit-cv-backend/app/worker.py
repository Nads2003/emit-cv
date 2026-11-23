"""Processus worker : traite la file de tâches (analyses de CV, calculs de classement).

    python -m app.worker                 # un worker
    docker compose up --scale worker=3   # plusieurs workers (ils se partagent la file sans conflit)

Variables : WORKER_BATCH (tâches réservées à la fois), WORKER_POLL_S (pause quand la file est vide), WORKER_VERROU_S (reprise d'une tâche bloquée)."""
import logging
import signal
import time
from pathlib import Path

from app.core.config import settings
from app.db.base import Base
from app.db.session import engine
from app.services import taches

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s : %(message)s")
log = logging.getLogger("emit.worker")
HEARTBEAT = Path("/tmp/worker_alive")  # lu par le healthcheck Docker
_stop = False


def _arret(*_):
    global _stop
    _stop = True
    log.info("Arrêt demandé : fin de la tâche en cours puis sortie.")


def main() -> None:
    signal.signal(signal.SIGTERM, _arret)
    signal.signal(signal.SIGINT, _arret)
    if settings.environment != "production":
        Base.metadata.create_all(engine)
    log.info("Worker %s démarré (lot=%s, pause=%ss)", taches.WORKER_ID, settings.worker_batch, settings.worker_poll_s)
    while not _stop:
        HEARTBEAT.touch()
        try:
            n = taches.traiter_lot()
        except Exception:
            log.exception("Erreur dans la boucle du worker")
            n = 0
        if n == 0:
            time.sleep(settings.worker_poll_s)
    log.info("Worker arrêté proprement.")


if __name__ == "__main__":
    main()
