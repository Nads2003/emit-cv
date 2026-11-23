"""Inscription réservée aux étudiants autorisés, vérification d'e-mail, unicité, messages non révélateurs, limitation de débit."""
from datetime import timedelta

from sqlalchemy import select

from app.core.config import settings
from app.db.session import SessionLocal
from app.models import EtudiantAutorise, Etudiant, InscriptionEnAttente, Utilisateur, utcnow
from app.services import email as mail
from tests.conftest import autoriser, token_dans_dernier_email

API = "/api/v1"
BON = {"nom": "RAKOTO", "prenom": "Hery", "email": "hery@emit-test.mg", "matricule": "EMIT-001", "mot_de_passe": "Motdepasse1", "mention_id": 1}


def setup_autorise():
    autoriser("RAKOTO", "Hery", "hery@emit-test.mg", "EMIT-001")


def test_inscription_autorisee_parcours_complet(client):
    setup_autorise()
    r = client.post(f"{API}/auth/inscription", json=BON)
    assert r.status_code == 202 and "e-mail" in r.json()["message"]
    assert len(mail.OUTBOX) == 1 and mail.OUTBOX[0]["to"] == "hery@emit-test.mg" and "/verification?token=" in mail.OUTBOX[0]["body"]
    # AUCUN compte tant que l'e-mail n'est pas vérifié
    with SessionLocal() as db:
        assert db.scalar(select(Utilisateur).where(Utilisateur.email == "hery@emit-test.mg")) is None
    assert client.post(f"{API}/auth/connexion", json={"email": "hery@emit-test.mg", "mot_de_passe": "Motdepasse1"}).status_code == 401
    v = client.post(f"{API}/auth/verification", json={"token": token_dans_dernier_email(), "mot_de_passe": "Motdepasse1"})
    assert v.status_code == 201 and v.json()["utilisateur"]["role"] == "etudiant" and v.json()["utilisateur"]["nom"] == "Hery RAKOTO"
    assert "httponly" in v.headers["set-cookie"].lower()
    h = {"Authorization": f"Bearer {v.json()['access_token']}"}
    assert client.get(f"{API}/etudiants/moi", headers=h).json()["matricule"] == "EMIT-001"
    assert client.post(f"{API}/auth/connexion", json={"email": "hery@emit-test.mg", "mot_de_passe": "Motdepasse1"}).status_code == 200
    with SessionLocal() as db:
        a = db.scalar(select(EtudiantAutorise))
        assert a.utilisateur_id is not None and db.scalar(select(InscriptionEnAttente)) is None  # entrée consommée, attente purgée


def test_etudiant_non_autorise_refuse_cote_serveur(client):
    setup_autorise()
    r = client.post(f"{API}/auth/inscription", json={**BON, "email": "intrus@emit-test.mg", "matricule": "EMIT-999"})
    assert r.status_code == 403 and not mail.OUTBOX
    with SessionLocal() as db:
        assert db.scalar(select(Utilisateur).where(Utilisateur.email == "intrus@emit-test.mg")) is None


def test_matricule_et_email_doivent_correspondre_a_la_meme_entree(client):
    setup_autorise()
    autoriser("RABE", "Lalaina", "lalaina@emit-test.mg", "EMIT-002")
    # e-mail d'un étudiant avec le matricule d'un AUTRE : usurpation refusée
    assert client.post(f"{API}/auth/inscription", json={**BON, "matricule": "EMIT-002"}).status_code == 403
    # identité correcte mais nom différent : refusé aussi
    assert client.post(f"{API}/auth/inscription", json={**BON, "nom": "AUTRE"}).status_code == 403
    assert not mail.OUTBOX
    # tolérance casse/accents/espaces sur le matricule, l'e-mail et le nom
    ok = client.post(f"{API}/auth/inscription", json={**BON, "email": "HERY@emit-test.mg", "matricule": " emit-001 ", "nom": "rakoto", "prenom": "HÉRY"})
    assert ok.status_code == 202


def test_matricule_deja_utilise_impossible_de_creer_un_second_compte(client, faire_etudiant):
    faire_etudiant("Hery Rakoto")  # crée un compte avec etu1@test.mg / MAT-001
    msgs = set()
    for corps in ({"nom": "Rakoto", "prenom": "Hery", "email": "etu1@test.mg", "matricule": "MAT-001"},               # même identité
                  {"nom": "Rakoto", "prenom": "Hery", "email": "etu1@test.mg", "matricule": "MAT-001", "mention_id": 2},  # tentative avec autre mention
                  {"nom": "X", "prenom": "Y", "email": "etu1@test.mg", "matricule": "MAT-001"}):                         # nom usurpé
        r = client.post(f"{API}/auth/inscription", json={"mot_de_passe": "Motdepasse1", "mention_id": 1, **corps})
        assert r.status_code == 403
        msgs.add(r.json()["detail"])
    # un seul message, quelle que soit la cause : on ne révèle ni l'existence ni l'état d'une entrée
    inconnu = client.post(f"{API}/auth/inscription", json={**BON, "email": "zz@emit-test.mg", "matricule": "ZZZ-1"})
    assert msgs == {inconnu.json()["detail"]}
    with SessionLocal() as db:
        assert len(db.scalars(select(Etudiant)).all()) == 1


def test_contraintes_d_unicite_en_base(client):
    from sqlalchemy.exc import IntegrityError
    setup_autorise()
    with SessionLocal() as db:
        db.add(EtudiantAutorise(nom="A", prenom="B", email="hery@emit-test.mg", matricule="AUTRE-1"))
        try:
            db.commit()
            assert False, "l'unicité de l'e-mail aurait dû être refusée"
        except IntegrityError:
            db.rollback()
        db.add(EtudiantAutorise(nom="A", prenom="B", email="autre@emit-test.mg", matricule="EMIT-001"))
        try:
            db.commit()
            assert False, "l'unicité du matricule aurait dû être refusée"
        except IntegrityError:
            db.rollback()


def test_verification_jeton_invalide_expire_reutilise_ou_mauvais_mot_de_passe(client):
    setup_autorise()
    client.post(f"{API}/auth/inscription", json=BON)
    tok = token_dans_dernier_email()
    assert client.post(f"{API}/auth/verification", json={"token": "x" * 40, "mot_de_passe": "Motdepasse1"}).status_code == 400
    # le jeton seul ne suffit pas : il faut aussi le mot de passe choisi (protège d'une inscription forgée par un tiers)
    assert client.post(f"{API}/auth/verification", json={"token": tok, "mot_de_passe": "Mauvais123"}).status_code == 400
    ok = client.post(f"{API}/auth/verification", json={"token": tok, "mot_de_passe": "Motdepasse1"})
    assert ok.status_code == 201
    assert client.post(f"{API}/auth/verification", json={"token": tok, "mot_de_passe": "Motdepasse1"}).status_code == 400  # usage unique


def test_jeton_expire(client):
    setup_autorise()
    client.post(f"{API}/auth/inscription", json=BON)
    with SessionLocal() as db:
        p = db.scalar(select(InscriptionEnAttente))
        p.expire_le = utcnow() - timedelta(minutes=1)
        db.commit()
    assert client.post(f"{API}/auth/verification", json={"token": token_dans_dernier_email(), "mot_de_passe": "Motdepasse1"}).status_code == 400


def test_trop_d_essais_de_mot_de_passe_invalide_le_jeton(client):
    setup_autorise()
    client.post(f"{API}/auth/inscription", json=BON)
    tok = token_dans_dernier_email()
    for _ in range(settings.verif_max_tentatives):
        client.post(f"{API}/auth/verification", json={"token": tok, "mot_de_passe": "Mauvais123"})
    assert client.post(f"{API}/auth/verification", json={"token": tok, "mot_de_passe": "Motdepasse1"}).status_code == 400  # jeton détruit


def test_nouvelle_demande_remplace_l_ancien_lien(client):
    setup_autorise()
    client.post(f"{API}/auth/inscription", json=BON)
    ancien = token_dans_dernier_email()
    client.post(f"{API}/auth/inscription", json=BON)
    assert client.post(f"{API}/auth/verification", json={"token": ancien, "mot_de_passe": "Motdepasse1"}).status_code == 400
    assert client.post(f"{API}/auth/verification", json={"token": token_dans_dernier_email(), "mot_de_passe": "Motdepasse1"}).status_code == 201


def test_validation_des_donnees_recues(client):
    setup_autorise()
    for corps, mot in [({"mot_de_passe": "court"}, "8 caractères"), ({"email": "pas-un-email"}, ""), ({"matricule": "a b"}, ""), ({"mention_id": None}, ""), ({"nom": ""}, "")]:
        r = client.post(f"{API}/auth/inscription", json={**BON, **corps})
        assert r.status_code == 422 and (mot in r.text)
    assert client.post(f"{API}/auth/inscription", json={**BON, "mention_id": 9999}).status_code == 422


def test_role_non_modifiable_par_le_client(client):
    setup_autorise()
    client.post(f"{API}/auth/inscription", json={**BON, "role": "admin"})
    v = client.post(f"{API}/auth/verification", json={"token": token_dans_dernier_email(), "mot_de_passe": "Motdepasse1"})
    assert v.json()["utilisateur"]["role"] == "etudiant"


def test_limitation_des_tentatives_d_inscription(client, monkeypatch):
    monkeypatch.setattr(settings, "inscription_limit", 3)
    codes = [client.post(f"{API}/auth/inscription", json={**BON, "matricule": f"INC-{i}"}).status_code for i in range(5)]
    assert codes[:3] == [403, 403, 403] and codes[3:] == [429, 429]


def test_limitation_par_matricule(client, monkeypatch):
    monkeypatch.setattr(settings, "inscription_limit_matricule", 2)
    codes = [client.post(f"{API}/auth/inscription", json={**BON, "matricule": "CIBLE-1"}).status_code for _ in range(4)]
    assert codes == [403, 403, 429, 429]
