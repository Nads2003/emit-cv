#!/bin/sh
# Teste QU'UNE SAUVEGARDE SE RESTAURE VRAIMENT : restauration dans une base jetable, contrôle des données, suppression.
# À exécuter régulièrement (une sauvegarde jamais testée n'est pas une sauvegarde).   Local : PGHOST/PGUSER/PGPASSWORD requis.
set -eu
DUMP="${1:?usage: verifier_sauvegarde.sh fichier.dump}"; TMP="emit_verif_$$"
"$(dirname "$0")/restore_db.sh" "$DUMP" "$TMP" > /dev/null
N=$(psql -d "$TMP" -tAc "SELECT count(*) FROM information_schema.tables WHERE table_schema='public'")
U=$(psql -d "$TMP" -tAc "SELECT count(*) FROM utilisateur"); C=$(psql -d "$TMP" -tAc "SELECT count(*) FROM cv")
dropdb "$TMP"
echo "OK : $N tables, $U utilisateurs, $C CV restaurés depuis $(basename "$DUMP")"
[ "$N" -ge 30 ] || { echo "ÉCHEC : schéma incomplet" >&2; exit 1; }
