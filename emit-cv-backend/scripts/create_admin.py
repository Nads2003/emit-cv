"""Crée un compte administrateur EMIT (il n'existe aucune inscription publique pour ce rôle).

Usage :  python -m scripts.create_admin --email admin@emit.mg --nom "Admin EMIT"
         (le mot de passe est demandé de façon masquée ; ou --password pour l'automatisation)
"""
import argparse
import getpass
import sys

from sqlalchemy import select

from app.core.security import hash_password
from app.db.base import Base
from app.db.session import SessionLocal, engine
from app import models  # noqa: F401
from app.models import Administrateur, Utilisateur
from app.schemas.auth import valider_mot_de_passe


def creer_admin(email: str, nom: str, password: str, poste: str = "Administrateur EMIT") -> Administrateur:
    valider_mot_de_passe(password)
    Base.metadata.create_all(engine)
    with SessionLocal() as db:
        if db.scalar(select(Utilisateur.id).where(Utilisateur.email == email.lower())):
            raise SystemExit(f"Un compte existe déjà avec l'e-mail {email}.")
        admin = Administrateur(nom=nom, email=email.lower(), mot_de_passe_hash=hash_password(password), poste=poste)
        db.add(admin)
        db.commit()
        db.refresh(admin)
        return admin


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--email", required=True)
    p.add_argument("--nom", default="Administrateur EMIT")
    p.add_argument("--password")
    a = p.parse_args()
    pwd = a.password or getpass.getpass("Mot de passe : ")
    if not a.password and pwd != getpass.getpass("Confirmer : "):
        sys.exit("Les mots de passe ne correspondent pas.")
    admin = creer_admin(a.email, a.nom, pwd)
    print(f"Administrateur créé : {admin.email} (id {admin.id})")


if __name__ == "__main__":
    main()
