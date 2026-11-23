"""Import CLI de la liste officielle des étudiants (équivalent de l'écran admin, avec aperçu puis confirmation).

    python -m scripts.import_etudiants liste.xlsx --admin-email admin@emit.mg            # aperçu seulement
    python -m scripts.import_etudiants liste.xlsx --admin-email admin@emit.mg --confirmer  # applique
    (--ignorer-erreurs pour appliquer malgré des lignes invalides, qui sont alors ignorées)"""
import argparse
import sys
from pathlib import Path

from sqlalchemy import select

from app.db.session import SessionLocal
from app import models  # noqa: F401
from app.models import Administrateur
from app.services import acces


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("fichier")
    p.add_argument("--admin-email", required=True)
    p.add_argument("--confirmer", action="store_true")
    p.add_argument("--ignorer-erreurs", action="store_true")
    a = p.parse_args()
    with SessionLocal() as db:
        admin = db.scalar(select(Administrateur).where(Administrateur.email == a.admin_email.lower()))
        if not admin:
            sys.exit("Administrateur introuvable.")
        imp = acces.apercu_import(db, admin, Path(a.fichier).name, Path(a.fichier).read_bytes())
        print(f"Aperçu #{imp.id} : {imp.nb_lignes} lignes — {imp.nb_nouveaux} nouveaux, {imp.nb_maj} mises à jour, {imp.nb_inchanges} inchangés, {imp.nb_erreurs} erreurs")
        for l in db.scalars(select(models.ImportLigne).where(models.ImportLigne.import_id == imp.id, models.ImportLigne.action == "erreur").limit(30)):
            print(f"  ligne {l.numero} : {l.message}")
        if a.confirmer:
            imp = acces.confirmer_import(db, admin, imp.id, a.ignorer_erreurs)
            print(f"Import appliqué : {imp.nb_nouveaux} ajoutés, {imp.nb_maj} mis à jour.")
        else:
            print("Rien n'a été appliqué (relancez avec --confirmer).")


if __name__ == "__main__":
    main()
