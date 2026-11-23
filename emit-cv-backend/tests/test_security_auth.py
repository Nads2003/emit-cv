import time

import jwt

from app.core.config import settings
from app.core.security import create_token, decode_token, hash_password, verify_password

API = "/api/v1"


def test_hash_argon2_et_verification():
    h = hash_password("Secret123")
    assert h != "Secret123" and h.startswith("$argon2")
    assert verify_password("Secret123", h) and not verify_password("autre", h)


def test_jetons_type_et_expiration():
    t = create_token(7, "access")
    assert decode_token(t, "access") == 7
    assert decode_token(t, "refresh") is None  # un access token ne peut pas servir de refresh
    expire = jwt.encode({"sub": "7", "type": "access", "exp": int(time.time()) - 5}, settings.secret_key, algorithm="HS256")
    assert decode_token(expire, "access") is None
    assert decode_token("n.importe.quoi", "access") is None
    forge = jwt.encode({"sub": "7", "type": "access", "exp": int(time.time()) + 600}, "autre-secret", algorithm="HS256")
    assert decode_token(forge, "access") is None  # signature invalide


def test_connexion_mauvais_identifiants_message_identique(client):
    a = client.post(f"{API}/auth/connexion", json={"email": "admin@emit.mg", "mot_de_passe": "faux"})
    b = client.post(f"{API}/auth/connexion", json={"email": "inconnu@emit.mg", "mot_de_passe": "faux"})
    assert a.status_code == b.status_code == 401 and a.json() == b.json()


def test_refresh_par_cookie_et_deconnexion(client):
    r = client.post(f"{API}/auth/connexion", json={"email": "admin@emit.mg", "mot_de_passe": "Admin12345"})
    assert "httponly" in r.headers["set-cookie"].lower()
    r = client.post(f"{API}/auth/refresh")
    assert r.status_code == 200 and r.json()["utilisateur"]["role"] == "admin"
    client.post(f"{API}/auth/deconnexion")
    client.cookies.clear()
    assert client.post(f"{API}/auth/refresh").status_code == 401


def test_separation_stricte_des_roles(client, admin, faire_etudiant):
    h, _ = faire_etudiant()
    # sans jeton / jeton invalide
    for url in ("/cvs", "/offres", "/admin/stats", "/admin/taches", "/admin/etudiants-autorises", "/notifications"):
        assert client.get(f"{API}{url}").status_code == 401, url
    assert client.get(f"{API}/cvs", headers={"Authorization": "Bearer faux"}).status_code == 401
    # ÉTUDIANT -> routes ADMIN : refusé
    for methode, url in [("get", "/admin/stats"), ("get", "/admin/historique"), ("get", "/admin/taches"), ("post", "/admin/taches/relancer-echouees"),
                         ("get", "/admin/etudiants-autorises"), ("get", "/admin/etudiants-autorises/imports"), ("get", "/etudiants"),
                         ("post", "/offres"), ("post", "/offres/1/recalculer"), ("get", "/offres/1/recommandations"), ("get", "/offres/1/runs"),
                         ("put", "/offres/1/candidats/1/statut")]:
        r = getattr(client, methode)(f"{API}{url}", headers=h, **({"json": {}} if methode in ("post", "put") else {}))
        assert r.status_code == 403, (methode, url, r.status_code)
    # ADMIN -> routes ÉTUDIANT : refusé
    for methode, url in [("get", "/cvs"), ("post", "/cvs"), ("get", "/etudiants/moi"), ("put", "/etudiants/moi/disponibilite"),
                         ("get", "/recommandations/moi"), ("get", "/candidatures/moi"), ("post", "/offres/1/postuler")]:
        r = getattr(client, methode)(f"{API}{url}", headers=admin, **({"json": {}} if methode in ("post", "put") else {}))
        assert r.status_code == 403, (methode, url, r.status_code)
    assert client.get(f"{API}/admin/stats", headers=admin).status_code == 200


def test_limitation_de_debit_connexion(client, monkeypatch):
    monkeypatch.setattr(settings, "login_rate_limit", 3)
    codes = [client.post(f"{API}/auth/connexion", json={"email": "x@test.mg", "mot_de_passe": "faux"}).status_code for _ in range(5)]
    assert codes[:3] == [401, 401, 401] and codes[3:] == [429, 429]


def test_verrouillage_temporaire_du_compte_apres_echecs(client, monkeypatch):
    monkeypatch.setattr(settings, "login_echecs_compte", 3)
    codes = [client.post(f"{API}/auth/connexion", json={"email": "admin@emit.mg", "mot_de_passe": "faux"}).status_code for _ in range(5)]
    assert codes[:3] == [401, 401, 401] and codes[3:] == [429, 429]
    # même avec le BON mot de passe, le compte reste verrouillé le temps de la fenêtre (protège contre le brute-force)
    assert client.post(f"{API}/auth/connexion", json={"email": "admin@emit.mg", "mot_de_passe": "Admin12345"}).status_code == 429


def test_en_tetes_de_securite_et_sante(client):
    r = client.get("/health")
    assert r.headers["x-content-type-options"] == "nosniff" and r.headers["x-frame-options"] == "DENY" and r.headers["x-request-id"]
    d = client.get("/ready")
    assert d.status_code == 200 and d.json()["status"] == "ok"
