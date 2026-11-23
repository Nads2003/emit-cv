"""Point d'entrée FastAPI."""
import json
import logging
import time
import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI, Response
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from starlette.middleware.base import BaseHTTPMiddleware

from app import models  # noqa: F401  (enregistre les tables)
from app.api.v1 import admin_acces, auth, cvs, divers, etudiants, offres, suivi
from app.core.config import settings
from app.core.errors import register_error_handlers
from app.db.base import Base
from app.db.session import SessionLocal, engine
from app.services import taches
from app.services.referentiels import seed_referentiels


class JsonFormatter(logging.Formatter):
    def format(self, record):
        d = {"t": self.formatTime(record), "niveau": record.levelname, "logger": record.name, "msg": record.getMessage()}
        if record.exc_info:
            d["exc"] = self.formatException(record.exc_info)
        return json.dumps(d, ensure_ascii=False)


_h = logging.StreamHandler()
_h.setFormatter(JsonFormatter() if settings.log_json else logging.Formatter("%(asctime)s %(levelname)s %(name)s : %(message)s"))
logging.basicConfig(level=logging.INFO, handlers=[_h], force=True)
log = logging.getLogger("emit")


@asynccontextmanager
async def lifespan(_: FastAPI):
    if settings.environment == "production":
        if settings.secret_key.startswith("change-me") or len(settings.secret_key) < 32:
            raise RuntimeError("SECRET_KEY non sécurisée : définissez une valeur aléatoire d'au moins 32 caractères.")
        if settings.email_backend != "smtp":
            log.warning("EMAIL_BACKEND n'est pas « smtp » : les e-mails de vérification ne seront PAS envoyés.")
        if not settings.cookie_secure:
            log.warning("COOKIE_SECURE=false en production : activez-le (HTTPS obligatoire).")
    else:
        Base.metadata.create_all(engine)  # en production : `alembic upgrade head`
    with SessionLocal() as db:
        seed_referentiels(db)
    yield


class Middleware(BaseHTTPMiddleware):
    """En-têtes de sécurité + identifiant de requête + journal des requêtes lentes ou en erreur."""

    async def dispatch(self, request, call_next):
        rid = request.headers.get("x-request-id") or uuid.uuid4().hex[:12]
        t0 = time.perf_counter()
        response = await call_next(request)
        ms = (time.perf_counter() - t0) * 1000
        response.headers["X-Request-ID"] = rid
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("X-Frame-Options", "DENY")
        response.headers.setdefault("Referrer-Policy", "no-referrer")
        if request.url.path.startswith("/api"):
            response.headers.setdefault("Cache-Control", "no-store")
        if settings.cookie_secure:
            response.headers.setdefault("Strict-Transport-Security", "max-age=31536000; includeSubDomains")
        if response.status_code >= 500 or ms > 1500:
            log.warning("requete rid=%s %s %s -> %s en %.0f ms", rid, request.method, request.url.path, response.status_code, ms)
        return response


app = FastAPI(title=settings.app_name, version="2.0.0", lifespan=lifespan,
              description="API de gestion de CV et de recommandation de candidats à l'EMIT, assistée par IA.",
              docs_url="/docs" if settings.environment != "production" else None, redoc_url=None)
app.add_middleware(Middleware)
app.add_middleware(CORSMiddleware, allow_origins=settings.cors_origins, allow_credentials=True,
                   allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"], allow_headers=["Authorization", "Content-Type"])
register_error_handlers(app)

for r in (auth.router, etudiants.router, cvs.router, offres.router, suivi.router, admin_acces.router, divers.notifications, divers.referentiels):
    app.include_router(r, prefix="/api/v1")


@app.get("/health", tags=["Système"], summary="Liveness : le processus répond")
def health():
    return {"status": "ok"}


@app.get("/ready", tags=["Système"], summary="Readiness : base de données joignable (+ état de la file de tâches)")
def ready(response: Response):
    try:
        with SessionLocal() as db:
            db.execute(text("SELECT 1"))
            file_ = taches.resume(db)
    except Exception:
        log.exception("Base de données injoignable")
        response.status_code = 503
        return {"status": "indisponible"}
    return {"status": "ok", "taches": file_}
