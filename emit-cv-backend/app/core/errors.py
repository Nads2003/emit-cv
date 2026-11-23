"""Gestion centralisée des erreurs : réponses JSON homogènes, messages en français."""
import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

log = logging.getLogger("emit")


def register_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(StarletteHTTPException)
    async def http_exc(_: Request, exc: StarletteHTTPException):
        return JSONResponse({"detail": exc.detail}, status_code=exc.status_code, headers=getattr(exc, "headers", None))

    @app.exception_handler(RequestValidationError)
    async def validation_exc(_: Request, exc: RequestValidationError):
        erreurs = []
        for e in exc.errors():
            champ = ".".join(str(p) for p in e["loc"] if p not in ("body", "query", "path"))
            erreurs.append({"champ": champ, "message": e["msg"].replace("Value error, ", "")})
        return JSONResponse({"detail": "Données invalides.", "erreurs": erreurs}, status_code=422)

    @app.exception_handler(Exception)
    async def unhandled(_: Request, exc: Exception):
        log.exception("Erreur non gérée : %s", exc)
        return JSONResponse({"detail": "Erreur interne du serveur."}, status_code=500)
