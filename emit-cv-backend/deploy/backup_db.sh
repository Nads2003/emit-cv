#!/bin/sh
# Sauvegarde de la base PostgreSQL (+ fichiers de CV) avec rotation.
#   Local   : PGHOST=... PGUSER=emit PGPASSWORD=... PGDATABASE=emit_cv ./deploy/backup_db.sh
#   Docker  : COMPOSE=1 ./deploy/backup_db.sh        (depuis la racine du projet)
# Variables : BACKUP_DIR (défaut ./backups) · KEEP_DAILY (14 jours) · KEEP_WEEKLY (8 semaines, sauvegardes du dimanche)
# Planification (cron, tous les jours à 02h30) :  30 2 * * *  cd /opt/emit-cv-ia && COMPOSE=1 ./deploy/backup_db.sh >> backups/backup.log 2>&1
set -eu
BACKUP_DIR="${BACKUP_DIR:-./backups}"; KEEP_DAILY="${KEEP_DAILY:-14}"; KEEP_WEEKLY="${KEEP_WEEKLY:-8}"
STAMP="$(date +%Y%m%d_%H%M%S)"; DUMP="$BACKUP_DIR/emit_cv_$STAMP.dump"
mkdir -p "$BACKUP_DIR"
if [ "${COMPOSE:-0}" = "1" ]; then
  docker compose exec -T db pg_dump -U emit -d emit_cv -Fc --no-owner > "$DUMP"
else
  pg_dump -Fc --no-owner -f "$DUMP"
fi
# 1) la sauvegarde est lisible ? 2) somme de contrôle pour détecter une corruption ultérieure
pg_restore --list "$DUMP" > /dev/null 2>&1 || { [ "${COMPOSE:-0}" = "1" ] && docker compose exec -T db pg_restore --list < "$DUMP" >/dev/null; } || { echo "ÉCHEC : sauvegarde illisible, supprimée" >&2; rm -f "$DUMP"; exit 1; }
( cd "$BACKUP_DIR" && sha256sum "$(basename "$DUMP")" > "$(basename "$DUMP").sha256" )
# Fichiers de CV (hors base) : archive de l'espace de stockage si accessible
if [ "${COMPOSE:-0}" = "1" ]; then
  docker compose exec -T backend tar -czf - -C /app uploads > "$BACKUP_DIR/uploads_$STAMP.tar.gz" 2>/dev/null || echo "avertissement : archive des fichiers non créée" >&2
elif [ -d "${UPLOAD_DIR:-./uploads}" ]; then
  tar -czf "$BACKUP_DIR/uploads_$STAMP.tar.gz" -C "$(dirname "${UPLOAD_DIR:-./uploads}")" "$(basename "${UPLOAD_DIR:-./uploads}")"
fi
# Rotation : on garde KEEP_DAILY jours de sauvegardes + celles du dimanche pendant KEEP_WEEKLY semaines
find "$BACKUP_DIR" -name 'emit_cv_*.dump*' -mtime +"$KEEP_DAILY" | while read -r f; do
  d="$(basename "$f" | sed -E 's/emit_cv_([0-9]{8}).*/\1/')"
  if [ "$(date -d "$d" +%u 2>/dev/null || echo 0)" = "7" ] && [ -n "$(find "$f" -mtime -$((KEEP_WEEKLY * 7)) 2>/dev/null)" ]; then continue; fi
  rm -f "$f"
done
find "$BACKUP_DIR" -name 'uploads_*.tar.gz' -mtime +"$KEEP_DAILY" -delete
echo "OK : $DUMP ($(du -h "$DUMP" | cut -f1))"
