from datetime import date, timedelta

API = "/api/v1"

OFFRE = {
    "titre": "Stage Développeur Backend IA", "type": "stage", "publier": True,
    "description": "Conception d'API REST et d'un moteur de recommandation basé sur l'IA.",
    "criteres": [
        {"competence": "Python", "poids": 5, "niveau_requis": "avance", "obligatoire": True},
        {"competence": "FastAPI", "poids": 3, "niveau_requis": "intermediaire"},
        {"competence": "PostgreSQL", "poids": 2, "niveau_requis": "intermediaire"},
    ],
}


def preparer(client, faire_etudiant, publier_cv):
    h_bon, id_bon = faire_etudiant("Bon Candidat")
    h_moyen, id_moyen = faire_etudiant("Candidat Moyen")
    h_faible, id_faible = faire_etudiant("Candidat Faible", mention="Gestion", niveau="L3")
    publier_cv(h_faible, "Comptable", [("Comptabilité", "avance"), ("Excel", "expert")])
    publier_cv(h_bon, "Développeur Python", [("Python", "expert"), ("FastAPI", "avance"), ("PostgreSQL", "avance")])
    publier_cv(h_moyen, "Développeur web", [("JavaScript", "avance"), ("Python", "debutant")])
    return (h_bon, id_bon), (h_moyen, id_moyen), (h_faible, id_faible)


def test_classement_ia_ordonne_les_candidats(client, admin, faire_etudiant, publier_cv):
    (h_bon, id_bon), (_, id_moyen), (_, id_faible) = preparer(client, faire_etudiant, publier_cv)
    r = client.post(f"{API}/offres", json=OFFRE, headers=admin)
    assert r.status_code == 201 and r.json()["statut"] == "publiee"
    oid = r.json()["id"]
    c = client.get(f"{API}/offres/{oid}/recommandations", headers=admin).json()
    assert c["total"] == 3 and c["moteur_ia"] == "tfidf" and c["version_algorithme"] == "2.0.0" and c["run_id"]
    ordre = [i["etudiant"]["id"] for i in c["items"]]
    assert ordre == [id_bon, id_moyen, id_faible]
    scores = [i["score"] for i in c["items"]]
    assert scores[0] > 55 > scores[-1] and scores[0] > scores[1] > scores[2]
    top = c["items"][0]
    assert top["rang"] == 1 and not top["elimine"]
    comp = top["detail"]["criteres"]["competences"]
    assert {t["nom"] for t in comp["elements"]["trouvees"]} == {"Python", "FastAPI", "PostgreSQL"} and comp["elements"]["manquantes"] == []
    assert set(top["detail"]["criteres"]) == {"competences", "missions", "experience_projets", "specialite", "niveau_etudes", "disponibilite"}
    assert top["detail"]["points_forts"] and "points_a_verifier" in top["detail"] and "informations_manquantes" in top["detail"]
    assert "FastAPI" in c["items"][1]["detail"]["criteres"]["competences"]["elements"]["manquantes"]


def test_critere_obligatoire_manquant_penalise(client, admin, faire_etudiant, publier_cv):
    preparer(client, faire_etudiant, publier_cv)
    oid = client.post(f"{API}/offres", json=OFFRE, headers=admin).json()["id"]
    items = client.get(f"{API}/offres/{oid}/recommandations", headers=admin).json()["items"]
    faible = items[-1]
    # Règle de l'offre : critère obligatoire absent => « éliminé », classé après les conformes ; score conservé et visible
    assert faible["elimine"] and faible["detail"]["eligibilite"] == "elimine" and "Python" in faible["detail"]["exigences_non_respectees"][0]
    assert [i["elimine"] for i in items] == [False, True, True] and faible["score"] > 0


def test_filtres_et_recherche(client, admin, faire_etudiant, publier_cv):
    preparer(client, faire_etudiant, publier_cv)
    oid = client.post(f"{API}/offres", json=OFFRE, headers=admin).json()["id"]
    base = f"{API}/offres/{oid}/recommandations"
    assert client.get(base, params={"min_score": 60}, headers=admin).json()["total"] == 1
    assert client.get(base, params={"masquer_elimines": True}, headers=admin).json()["total"] == 1
    assert client.get(base, params={"q": "Moyen"}, headers=admin).json()["total"] == 1
    assert client.get(base, params={"competence": "python"}, headers=admin).json()["total"] == 2
    mentions = client.get(f"{API}/referentiels/mentions").json()
    gestion = next(m["id"] for m in mentions if m["nom"] == "Gestion")
    assert client.get(base, params={"mention_id": gestion}, headers=admin).json()["total"] == 1
    # recherche de profils (hors offre)
    r = client.get(f"{API}/etudiants", params={"competence": ["Python", "FastAPI"]}, headers=admin).json()
    assert r["total"] == 1 and r["items"][0]["nom"] == "Bon Candidat"
    assert client.get(f"{API}/etudiants", params={"q": "comptab"}, headers=admin).json()["total"] == 1


def test_le_classement_se_met_a_jour_quand_un_cv_est_publie(client, admin, faire_etudiant, publier_cv):
    oid = client.post(f"{API}/offres", json=OFFRE, headers=admin).json()["id"]
    assert client.get(f"{API}/offres/{oid}/recommandations", headers=admin).json()["total"] == 0
    h, _ = faire_etudiant()
    cv_id = publier_cv(h, "Dev", [("Python", "expert"), ("FastAPI", "avance")])
    assert client.get(f"{API}/offres/{oid}/recommandations", headers=admin).json()["total"] == 1
    client.post(f"{API}/cvs/{cv_id}/depublier", headers=h)  # retiré du matching
    assert client.get(f"{API}/offres/{oid}/recommandations", headers=admin).json()["total"] == 0


def test_cote_etudiant_recommandations_et_candidature(client, admin, faire_etudiant, publier_cv, monkeypatch):
    from app.core.config import settings
    monkeypatch.setattr(settings, "ai_notify_threshold", 50)
    (h_bon, id_bon), *_ = preparer(client, faire_etudiant, publier_cv)
    oid = client.post(f"{API}/offres", json=OFFRE, headers=admin).json()["id"]
    reco = client.get(f"{API}/recommandations/moi", headers=h_bon).json()
    assert len(reco) == 1 and reco[0]["rang"] == 1 and reco[0]["score"] > 55 and reco[0]["detail"]["criteres"]["competences"]["elements"]["trouvees"]
    notifs = client.get(f"{API}/notifications", headers=h_bon).json()
    assert notifs["non_lues"] >= 1 and "correspond" in notifs["items"][0]["message"]
    liste = client.get(f"{API}/offres", headers=h_bon).json()
    assert len(liste) == 1 and liste[0]["a_postule"] is False
    assert client.post(f"{API}/offres/{oid}/postuler", headers=h_bon).status_code == 201
    assert client.post(f"{API}/offres/{oid}/postuler", headers=h_bon).status_code == 409
    assert client.get(f"{API}/candidatures/moi", headers=h_bon).json()[0]["statut"] == "postule"
    assert client.get(f"{API}/notifications", headers=admin).json()["non_lues"] == 1  # l'admin est prévenu
    # valider puis sélectionner
    assert client.put(f"{API}/offres/{oid}/candidats/{id_bon}/statut", json={"statut": "valide"}, headers=admin).status_code == 200
    assert client.put(f"{API}/offres/{oid}/candidats/{id_bon}/statut", json={"statut": "selectionne"}, headers=admin).json()["statut"] == "selectionne"
    assert client.get(f"{API}/candidatures/moi", headers=h_bon).json()[0]["statut"] == "selectionne"
    assert client.delete(f"{API}/offres/{oid}/postuler", headers=h_bon).status_code == 409  # déjà traitée
    top = client.get(f"{API}/offres/{oid}/recommandations", headers=admin).json()["items"][0]
    assert top["statut_candidature"] == "selectionne" and top["a_postule"] is True
    # lecture / marquage des notifications
    n_id = client.get(f"{API}/notifications", headers=h_bon).json()["items"][0]["id"]
    assert client.patch(f"{API}/notifications/{n_id}/lu", headers=h_bon).status_code == 204
    assert client.patch(f"{API}/notifications/{n_id}/lu", headers=admin).status_code == 404  # pas la sienne


def test_selection_dun_recommande_qui_na_pas_postule(client, admin, faire_etudiant, publier_cv):
    (_, id_bon), *_ = preparer(client, faire_etudiant, publier_cv)
    oid = client.post(f"{API}/offres", json=OFFRE, headers=admin).json()["id"]
    assert client.put(f"{API}/offres/{oid}/candidats/{id_bon}/statut", json={"statut": "selectionne"}, headers=admin).status_code == 200
    item = client.get(f"{API}/offres/{oid}/recommandations", params={"seulement_candidats": True}, headers=admin).json()["items"][0]
    assert item["statut_candidature"] == "selectionne"  # l'administrateur reste décisionnaire, même sans candidature de l'étudiant
    assert client.put(f"{API}/offres/{oid}/candidats/99999/statut", json={"statut": "valide"}, headers=admin).status_code == 404


def test_postuler_exige_un_cv_publie(client, admin, faire_etudiant):
    h, _ = faire_etudiant()
    oid = client.post(f"{API}/offres", json=OFFRE, headers=admin).json()["id"]
    r = client.post(f"{API}/offres/{oid}/postuler", headers=h)
    assert r.status_code == 422 and "Publiez" in r.json()["detail"]


def test_cycle_de_vie_offre(client, admin, faire_etudiant, publier_cv):
    h, _ = faire_etudiant()
    publier_cv(h, "Dev", [("Python", "avance")])
    brouillon = client.post(f"{API}/offres", json={**OFFRE, "publier": False}, headers=admin).json()
    assert brouillon["statut"] == "brouillon"
    assert client.get(f"{API}/offres", headers=h).json() == []  # invisible pour les étudiants
    assert client.get(f"{API}/offres/{brouillon['id']}", headers=h).status_code == 404
    assert client.post(f"{API}/offres/{brouillon['id']}/postuler", headers=h).status_code == 404
    pub = client.post(f"{API}/offres/{brouillon['id']}/publier", headers=admin)
    assert pub.json()["statut"] == "publiee"
    assert client.delete(f"{API}/offres/{brouillon['id']}", headers=admin).status_code == 409
    maj = client.put(f"{API}/offres/{brouillon['id']}", json={**OFFRE, "titre": "Titre modifié", "criteres": OFFRE["criteres"][:1]}, headers=admin)
    assert maj.json()["titre"] == "Titre modifié" and len(maj.json()["criteres"]) == 1
    assert client.post(f"{API}/offres/{brouillon['id']}/cloturer", headers=admin).json()["statut"] == "cloturee"
    assert client.put(f"{API}/offres/{brouillon['id']}", json=OFFRE, headers=admin).status_code == 409
    assert client.get(f"{API}/offres", headers=h).json() == []
    assert client.post(f"{API}/offres/{brouillon['id']}/postuler", headers=h).status_code == 409
    n = client.post(f"{API}/offres/{brouillon['id']}/recalculer", headers=admin)
    assert n.status_code == 200


def test_offre_expiree_et_validation(client, admin, faire_etudiant, publier_cv):
    h, _ = faire_etudiant()
    publier_cv(h, "Dev", [("Python", "avance")])
    hier = (date.today() - timedelta(days=1)).isoformat()
    oid = client.post(f"{API}/offres", json={**OFFRE, "date_limite": hier}, headers=admin).json()["id"]
    assert client.post(f"{API}/offres/{oid}/postuler", headers=h).status_code == 409
    assert client.get(f"{API}/offres", headers=h).json() == []
    assert client.post(f"{API}/offres", json={"titre": "ab"}, headers=admin).status_code == 422
    assert client.post(f"{API}/offres", json={**OFFRE, "criteres": [{"competence": "X", "poids": 9}]}, headers=admin).status_code == 422
    assert client.post(f"{API}/offres", json={**OFFRE, "mention_ids": [999]}, headers=admin).status_code == 422
    assert client.post(f"{API}/offres", json={"titre": "Offre vide", "publier": True}, headers=admin).status_code == 422
    assert client.post(f"{API}/offres", json={**OFFRE, "periode_debut": "2027-05-01", "periode_fin": "2027-01-01"}, headers=admin).status_code == 422


def test_stats_et_historique_admin(client, admin, faire_etudiant, publier_cv):
    preparer(client, faire_etudiant, publier_cv)
    client.post(f"{API}/offres", json=OFFRE, headers=admin)
    s = client.get(f"{API}/admin/stats", headers=admin).json()
    assert s["etudiants"] == 3 and s["cv_publies"] == 3 and s["offres_publiees"] == 1
    h = client.get(f"{API}/admin/historique", headers=admin).json()
    assert any("Publication de l'offre" in x["action"] for x in h)


def test_tracabilite_version_poids_et_criteres_par_classement(client, admin, faire_etudiant, publier_cv):
    preparer(client, faire_etudiant, publier_cv)
    oid = client.post(f"{API}/offres", json={**OFFRE, "niveau_obligatoire": False}, headers=admin).json()["id"]
    client.post(f"{API}/offres/{oid}/recalculer", headers=admin)
    runs = client.get(f"{API}/offres/{oid}/runs", headers=admin).json()
    assert len(runs) == 2 and runs[0]["statut"] == "termine" and runs[0]["version_algorithme"] == "2.0.0"
    assert sum(runs[0]["poids"].values()) == 100 and runs[0]["nb_candidats"] == 3 and runs[0]["moteur_ia"] == "tfidf"
    assert [c["competence"] for c in runs[0]["criteres_offre"]["criteres"]] == ["Python", "FastAPI", "PostgreSQL"]
    items = client.get(f"{API}/offres/{oid}/recommandations", headers=admin).json()["items"]
    assert items[0]["detail"]["run_id"] == runs[0]["id"]  # chaque score est rattaché au calcul qui l'a produit


def test_niveau_obligatoire_vs_preference_dans_l_api(client, admin, faire_etudiant, publier_cv):
    h, eid = faire_etudiant("Etu Niveau", niveau="L3")
    publier_cv(h, "Dev", [("Python", "expert"), ("FastAPI", "avance"), ("PostgreSQL", "avance")])
    mentions = client.get(f"{API}/referentiels/mentions").json()
    m1 = next(m for m in mentions if m["nom"] == "Informatique")
    m2_id = next(n["id"] for n in m1["niveaux"] if n["nom"] == "M2")
    base = {**OFFRE, "niveau_min_id": m2_id}
    pref = client.post(f"{API}/offres", json={**base, "niveau_obligatoire": False}, headers=admin).json()["id"]
    oblig = client.post(f"{API}/offres", json={**base, "niveau_obligatoire": True}, headers=admin).json()["id"]
    a = client.get(f"{API}/offres/{pref}/recommandations", headers=admin).json()["items"][0]
    b = client.get(f"{API}/offres/{oblig}/recommandations", headers=admin).json()["items"][0]
    assert not a["elimine"] and a["detail"]["criteres"]["niveau_etudes"]["statut"] == "partiel"
    assert b["elimine"] and "éliminatoire" in b["detail"]["exigences_non_respectees"][0] and a["score"] == b["score"]
