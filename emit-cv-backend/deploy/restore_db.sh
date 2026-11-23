#!/bin/sh
# Restaure une sauvegarde dans une base (créée si besoin). ATTENTION : écrase le contenu de la base cible.
#   ./deploy/restore_db.sh backups/emit_cv_20261030_023000.dump [base_cible]
# Local : PGHOST/PGUSER/PGPASSWORD requis. Docker : COMPOSE=1 (restaure dans le conteneur « db »).
set -eu
DUMP="${1:?usage: restore_db.sh fichier.dump [base_cible]}"; CIBLE="${2:-emit_cv}"
[ -f "$DUMP" ] || { echo "Fichier introuvable : $DUMP" >&2; exit 1; }
if [ -f "$DUMP.sha256" ]; then ( cd "$(dirname "$DUMP")" && sha256sum -c "$(basename "$DUMP").sha256" ) || { echo "Somme de contrôle invalide : sauvegarde corrompue" >&2; exit 1; }; fi
if [ "${COMPOSE:-0}" = "1" ]; then
  docker compose exec -T db psql -U emit -d postgres -tc "SELECT 1 FROM pg_database WHERE datname='$CIBLE'" | grep -q 1 || docker compose exec -T db createdb -U emit "$CIBLE"
  docker compose exec -T db pg_restore -U emit -d "$CIBLE" --clean --if-exists --no-owner < "$DUMP"
else
  psql -d postgres -tc "SELECT 1 FROM pg_database WHERE datname='$CIBLE'" | grep -q 1 || createdb "$CIBLE"
  pg_restore -d "$CIBLE" --clean --if-exists --no-owner "$DUMP"
fi
echo "Restauration terminée dans la base « $CIBLE »."
