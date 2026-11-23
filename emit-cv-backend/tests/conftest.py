"""Fixtures : base SQLite temporaire, moteur IA TF-IDF (pas de téléchargement de modèle), client HTTP."""
import os
import tempfile

_tmp = tempfile.mkdtemp(prefix="emit_tests_")
# TEST_DATABASE_URL permet de lancer la suite sur PostgreSQL ; par défaut : SQLite temporaire.
os.environ.update({
    "DATABASE_URL": os.environ.get("TEST_DATABASE_URL", f"sqlite:///{_tmp}/test.db"), "UPLOAD_DIR": f"{_tmp}/uploads", "AI_BACKEND": "tfidf",
    "SECRET_KEY": "test-secret-test-secret-test-secret-0000", "ENVIRONMENT": "test", "LOGIN_RATE_LIMIT": "1000",
    "TACHES_MODE": "inline", "INSCRIPTION_LIMIT": "1000", "INSCRIPTION_LIMIT_MATRICULE": "1000", "VERIF_LIMIT": "1000", "LOGIN_ECHECS_COMPTE": "1000",
})

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app import models  # noqa: E402,F401
from app.core import ratelimit  # noqa: E402
from app.services import email as mail  # noqa: E402
from app.core.security import hash_password  # noqa: E402
from app.db.base import Base  # noqa: E402
from app.db.session import SessionLocal, engine  # noqa: E402
from app.main import app  # noqa: E402
from app.models import Administrateur  # noqa: E402
from app.services.referentiels import seed_referentiels  # noqa: E402


@pytest.fixture(autouse=True)
def db_propre():
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    with SessionLocal() as db:
        seed_referentiels(db)
        db.add(Administrateur(nom="Admin Test", email="admin@emit.mg", mot_de_passe_hash=hash_password("Admin12345")))
        db.commit()
    with SessionLocal() as db:
        ratelimit.tout_effacer(db)
    mail.OUTBOX.clear()
    yield


@pytest.fixture
def client():
    return TestClient(app)


def _auth(client, email, mdp):
    r = client.post("/api/v1/auth/connexion", json={"email": email, "mot_de_passe": mdp})
    assert r.status_code == 200, r.text
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


@pytest.fixture
def admin(client):
    return _auth(client, "admin@emit.mg", "Admin12345")


def autoriser(nom, prenom, email, matricule):
    """Ajoute une entrée à la liste officielle des étudiants autorisés."""
    from app.models import EtudiantAutorise
    with SessionLocal() as db:
        db.add(EtudiantAutorise(nom=nom, prenom=prenom, email=email, matricule=matricule))
        db.commit()


def token_dans_dernier_email():
    import re
    m = re.search(r"token=([\w-]+)", mail.OUTBOX[-1]["body"])
    assert m, "aucun lien de vérification dans le dernier e-mail"
    return m.group(1)


@pytest.fixture
def faire_etudiant(client):
    """Fabrique : parcourt le VRAI parcours d'inscription (liste autorisée -> e-mail -> confirmation) et retourne (en-têtes, id)."""
    compteur = {"n": 0}

    def _make(nom="Étudiant Test", mention="Informatique", niveau="M1"):
        compteur["n"] += 1
        n = compteur["n"]
        prenom, _, famille = nom.partition(" ")
        famille = famille or "TEST"
        autoriser(famille, prenom, f"etu{n}@test.mg", f"MAT-{n:03d}")
        mentions = client.get("/api/v1/referentiels/mentions").json()
        m = next(x for x in mentions if x["nom"] == mention)
        niv = next(x for x in m["niveaux"] if x["nom"] == niveau)
        r = client.post("/api/v1/auth/inscription", json={"nom": famille, "prenom": prenom, "email": f"etu{n}@test.mg", "mot_de_passe": "Motdepasse1",
                                                          "matricule": f"MAT-{n:03d}", "mention_id": m["id"], "niveau_id": niv["id"]})
        assert r.status_code == 202, r.text
        v = client.post("/api/v1/auth/verification", json={"token": token_dans_dernier_email(), "mot_de_passe": "Motdepasse1"})
        assert v.status_code == 201, v.text
        return {"Authorization": f"Bearer {v.json()['access_token']}"}, v.json()["utilisateur"]["id"]

    return _make


@pytest.fixture
def publier_cv(client):
    """Crée et publie un CV pour un étudiant."""
    def _pub(headers, titre, competences, resume="Résumé de test suffisamment long pour la complétude du CV.", exp_mois=12):
        body = {
            "titre": titre, "resume": resume, "model_cv_id": 1,
            "competences": [{"nom": n, "niveau_maitrise": l} for n, l in competences],
            "formations": [{"diplome": "Master 1", "etablissement": "EMIT", "annee": 2025}],
            "experiences": [{"poste": "Stagiaire", "entreprise": "ACME", "date_debut": "2024-01-01",
                             "date_fin": f"{2024 + exp_mois // 12}-{1 + exp_mois % 12:02d}-01", "description": resume}],
        }
        r = client.post("/api/v1/cvs", json=body, headers=headers)
        assert r.status_code == 201, r.text
        cv_id = r.json()["id"]
        p = client.post(f"/api/v1/cvs/{cv_id}/publier", headers=headers)
        assert p.status_code == 200, p.text
        return cv_id
    return _pub
