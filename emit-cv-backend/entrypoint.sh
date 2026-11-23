#!/bin/sh
# Démarrage production : migrations -> (admin initial optionnel) -> Gunicorn + workers Uvicorn.
set -e
alembic upgrade head
if [ -n "$ADMIN_EMAIL" ] && [ -n "$ADMIN_PASSWORD" ]; then
  python -m scripts.create_admin --email "$ADMIN_EMAIL" --nom "${ADMIN_NOM:-Administrateur EMIT}" --password "$ADMIN_PASSWORD" || true
fi
# --max-requests : recyclage périodique des workers (limite les fuites mémoire) ; --graceful-timeout : fin propre des requêtes en cours
exec gunicorn app.main:app -k uvicorn.workers.UvicornWorker -w "${WEB_CONCURRENCY:-3}" -b 0.0.0.0:8000 \
  --timeout 60 --graceful-timeout 30 --max-requests 2000 --max-requests-jitter 200 --access-logfile - --forwarded-allow-ips="*"
