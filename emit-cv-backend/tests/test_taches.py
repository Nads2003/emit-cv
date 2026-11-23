"""File de tâches : état, coalescence, mode worker, échecs, reprise ciblée, récupération après interruption."""
from datetime import timedelta

import pytest
from sqlalchemy import select

from app.core.config import settings
from app.db.session import SessionLocal
from app.models import Tache, utcnow
from app.services import analyse as analyse_service, taches

API = "/api/v1"
OFFRE = {"titre": "Stage Développeur Backend IA", "type": "stage", "publier": True, "description": "Conception d'API REST et recommandation basée sur l'IA.",
         "criteres": [{"competence": "Python", "poids": 5, "niveau_requis": "avance", "obligatoire": False}]}


@pytest.fixture(autouse=True)
def sans_attente(monkeypatch):
    monkeypatch.setattr(taches, "BACKOFF_BASE_S", 0)


def test_coalescence_une_seule_tache_en_attente_par_cible(client):
    with SessionLocal() as db:
        a = taches.enqueue(db, "calcul_offre", 1, "x", priorite=6)
        b = taches.enqueue(db, "calcul_offre", 1, "y", priorite=2)
        c = taches.enqueue(db, "calcul_offre", 2, "z")
        assert a.id == b.id != c.id and b.priorite == 2
        assert db.scalar(select(Tache).where(Tache.id == a.id)).statut == "en_attente"


def test_mode_worker_rien_n_est_calcule_tant_que_le_worker_ne_passe_pas(client, admin, faire_etudiant, publier_cv, monkeypatch):
    monkeypatch.setattr(settings, "taches_mode", "worker")
    h, _ = faire_etudiant()
    publier_cv(h, "Dev", [("Python", "expert")])
    oid = client.post(f"{API}/offres", json=OFFRE, headers=admin).json()["id"]
    assert client.get(f"{API}/offres/{oid}/recommandations", headers=admin).json()["total"] == 0  # file d'attente, pas encore traitée
    etat = client.get(f"{API}/admin/taches", headers=admin).json()
    assert etat["resume"]["calcul_offre"]["en_attente"] == 1 and etat["resume"]["analyse_cv"]["en_attente"] >= 1
    assert taches.vider_la_file() >= 2  # ce que fait `python -m app.worker`
    assert client.get(f"{API}/offres/{oid}/recommandations", headers=admin).json()["total"] == 1
    etat = client.get(f"{API}/admin/taches", headers=admin).json()
    assert "en_attente" not in etat["resume"]["calcul_offre"] and etat["resume"]["calcul_offre"]["termine"] >= 1


def test_echec_nouvel_essai_puis_echoue_puis_relance_ciblee(client, admin, monkeypatch):
    monkeypatch.setattr(settings, "taches_mode", "worker")
    appels = {"n": 0, "casse": True}

    def instable(db, cv_id, forcer=False):
        appels["n"] += 1
        if appels["casse"]:
            raise RuntimeError("panne simulée")
        return {"statut": "ok", "change": False, "cache": False}

    monkeypatch.setattr(analyse_service, "analyser_cv", instable)
    with SessionLocal() as db:
        cass = taches.enqueue(db, "analyse_cv", 101, "test").id
        saine = taches.enqueue(db, "analyse_cv", 102, "test").id
    # la 2e tâche réussit pendant que la 1re échoue : une panne n'en bloque pas une autre
    appels["casse"] = False
    with SessionLocal() as db:
        db.get(Tache, saine).statut = "en_attente"
        db.get(Tache, cass).priorite = 1
        db.commit()
    appels["casse"] = True
    taches.executer(taches.reserver(SessionLocal(), "w", 1)[0])  # tâche cassée, essai 1 -> remise en attente
    with SessionLocal() as db:
        t = db.get(Tache, cass)
        assert (t.statut, t.tentatives) == ("en_attente", 1) and "panne simulée" in t.erreur
    taches.vider_la_file()  # essais 2 et 3 -> échouée
    with SessionLocal() as db:
        t = db.get(Tache, cass)
        assert (t.statut, t.tentatives) == ("echoue", settings.tache_max_tentatives)
        assert db.get(Tache, saine).statut == "echoue"  # (cassée aussi : même fonction instable) — on la rétablit pour la suite
    etat = client.get(f"{API}/admin/taches", params={"statut": "echoue"}, headers=admin).json()
    assert etat["resume"]["analyse_cv"]["echoue"] == 2 and all(r["erreur"] for r in etat["recentes"])
    # relance d'UNE seule tâche échouée, après réparation ; l'autre reste échouée (pas de retraitement inutile)
    appels["casse"], avant = False, appels["n"]
    assert client.post(f"{API}/admin/taches/{cass}/relancer", headers=admin).status_code == 200
    taches.vider_la_file()
    with SessionLocal() as db:
        assert db.get(Tache, cass).statut == "termine" and db.get(Tache, saine).statut == "echoue"
    assert appels["n"] - avant == 1
    assert client.post(f"{API}/admin/taches/{cass}/relancer", headers=admin).status_code == 409  # déjà terminée
    assert client.post(f"{API}/admin/taches/relancer-echouees", headers=admin).json() == {"relancees": 1}
    taches.vider_la_file()
    with SessionLocal() as db:
        assert db.get(Tache, saine).statut == "termine"


def test_reprise_apres_interruption_du_worker(client):
    with SessionLocal() as db:
        t = Tache(type="analyse_cv", cible_id=999, statut="en_cours", verrouille_par="worker-mort", verrou_expire_le=utcnow() - timedelta(minutes=1))
        vivant = Tache(type="analyse_cv", cible_id=998, statut="en_cours", verrouille_par="worker-vivant", verrou_expire_le=utcnow() + timedelta(minutes=10))
        db.add_all([t, vivant])
        db.commit()
        assert taches.recuperer_bloquees(db) == 1
        assert db.get(Tache, t.id).statut == "en_attente" and db.get(Tache, vivant.id).statut == "en_cours"


def test_deux_workers_ne_prennent_pas_la_meme_tache(client):
    with SessionLocal() as db:
        for i in range(6):
            taches.enqueue(db, "analyse_cv", 500 + i, "t")
        a = taches.reserver(db, "w1", 4)
        b = taches.reserver(db, "w2", 4)
    assert len(a) == 4 and len(b) == 2 and not set(a) & set(b)


def test_suivi_etat_cv_pour_l_etudiant(client, faire_etudiant, publier_cv):
    h, _ = faire_etudiant()
    cv_id = publier_cv(h, "Dev", [("Python", "expert")])
    assert client.get(f"{API}/cvs/{cv_id}", headers=h).json()["analyse"]["statut"] == "ok"
