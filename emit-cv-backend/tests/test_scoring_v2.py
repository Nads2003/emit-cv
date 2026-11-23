"""Scoring v2 : pondérations, formule, six critères, informations inconnues, exigences obligatoires, classement et justifications."""
from datetime import date

import pytest

from app.ai.embeddings import TfidfEngine
from app.ai.ranking import rank_candidates
from app.ai.scoring import (CRITERES, NOTE_INCONNU, POIDS, VERSION_ALGORITHME, CandidateData, ItemSims, OfferData, score_candidate)


def offre(**kw):
    base = dict(id=1, type="stage", titre="Stage Développeur Backend IA",
                missions="Conception d'API REST et intégration de modèles de recommandation pour une plateforme interne de gestion de candidats.",
                criteres=[{"competence": "Python", "poids": 5, "niveau_requis": "avance", "obligatoire": False},
                          {"competence": "FastAPI", "poids": 3, "niveau_requis": "intermediaire", "obligatoire": False}])
    base.update(kw)
    return OfferData(**base)


def cand(i=1, **kw):
    base = dict(etudiant_id=i, cv_id=i, competences=[{"nom": "Python", "niveau": "avance", "source": "declaree"}, {"nom": "FastAPI", "niveau": "avance", "source": "declaree"}],
                items=[{"genre": "experience", "titre": "Stagiaire développeur Orange", "texte": "conception api interne recommandation", "mois": 6}],
                mention_id=1, mention_nom="Informatique", niveau_rang=4, niveau_nom="M1", disponible=True)
    base.update(kw)
    return CandidateData(**base)


def sims(n=1, m=0.8, t=0.8):
    return ItemSims([m] * n, [t] * n)


# ---------------------------------------------------------------- pondérations et formule
def test_ponderations_totalisent_exactement_100():
    assert sum(POIDS.values()) == 100
    assert POIDS == {"competences": 40, "missions": 25, "experience_projets": 10, "specialite": 10, "niveau_etudes": 10, "disponibilite": 5}
    assert list(POIDS) == CRITERES and VERSION_ALGORITHME == "2.0.0"


def test_formule_somme_ponderee_verifiable():
    r = score_candidate(offre(), cand(), sims())
    attendu = sum(POIDS[k] * r.detail["criteres"][k]["note"] / 100 for k in CRITERES)
    assert r.score == pytest.approx(round(attendu, 1), abs=0.05)
    assert all(0 <= b["note"] <= 100 for b in r.detail["criteres"].values()) and 0 <= r.score <= 100
    assert sum(b["points"] for b in r.detail["criteres"].values()) == pytest.approx(r.score, abs=0.1)


def test_score_maximal_et_minimal_dans_les_bornes():
    parfait = score_candidate(offre(), cand(), sims(1, 1.0, 1.0))
    nul = score_candidate(offre(), cand(competences=[], items=[], niveau_rang=None, mention_id=None, disponible=False), ItemSims())
    assert 90 <= parfait.score <= 100 and 0 <= nul.score <= 20


# ---------------------------------------------------------------- critère 1 : compétences
def test_competences_niveau_synonymes_et_texte():
    off = offre()
    expert = score_candidate(off, cand(competences=[{"nom": "Postgres", "niveau": "expert", "source": "declaree"}, {"nom": "Python", "niveau": "expert", "source": "declaree"},
                                                    {"nom": "fast api", "niveau": "avance", "source": "declaree"}]), sims())
    debutant = score_candidate(off, cand(competences=[{"nom": "Python", "niveau": "debutant", "source": "declaree"}]), sims())
    texte = score_candidate(off, cand(competences=[{"nom": "Python", "niveau": None, "source": "texte"}]), sims())
    assert expert.detail["criteres"]["competences"]["note"] == 100  # « fast api » reconnu comme FastAPI
    assert 0 < debutant.detail["criteres"]["competences"]["note"] < 50
    assert 0 < texte.detail["criteres"]["competences"]["note"] < expert.detail["criteres"]["competences"]["note"]
    assert any("niveau n'est pas déclaré" in v for v in texte.detail["points_a_verifier"])


def test_competences_comportementales_identifiees():
    off = offre(criteres=[{"competence": "Communication", "poids": 2, "niveau_requis": "intermediaire", "obligatoire": False}])
    r = score_candidate(off, cand(competences=[{"nom": "Communication", "niveau": "avance", "source": "declaree"}]), sims())
    assert r.detail["criteres"]["competences"]["elements"]["trouvees"][0]["type"] == "comportementale"


def test_offre_sans_criteres_competences_deduites_ou_inconnues():
    off = OfferData(id=2, titre="Dev", missions="Nous cherchons un profil Python et Docker pour automatiser des déploiements.")
    r = score_candidate(off, cand(competences=[{"nom": "Python", "niveau": "avance", "source": "declaree"}, {"nom": "Docker", "niveau": "avance", "source": "declaree"}]), sims())
    assert r.detail["criteres_deduits"] and r.detail["criteres"]["competences"]["note"] == 100
    vide = score_candidate(OfferData(id=3, titre="X", missions=""), cand(), sims())
    assert vide.detail["criteres"]["competences"]["statut"] == "inconnu" and vide.detail["criteres"]["competences"]["note"] == NOTE_INCONNU


# ---------------------------------------------------------------- critères 2 et 3 : missions, expérience et projets
def test_missions_contenu_et_absence_d_experience():
    proche = score_candidate(offre(), cand(), sims(1, 0.9, 0.9))
    loin = score_candidate(offre(), cand(), sims(1, 0.05, 0.05))
    aucune = score_candidate(offre(), cand(items=[]), ItemSims())
    assert proche.detail["criteres"]["missions"]["note"] > 80 > loin.detail["criteres"]["missions"]["note"]
    assert aucune.detail["criteres"]["missions"]["statut"] == "absent" and aucune.detail["criteres"]["missions"]["note"] == 0
    assert "Aucune expérience ni projet renseigné." in aucune.detail["informations_manquantes"][0] or any("Aucun" in m for m in aucune.detail["informations_manquantes"])


def test_debutant_les_projets_contribuent_significativement():
    projets = [{"genre": "projet", "type": "academique", "titre": "Plateforme web de recommandation", "texte": "recommandation", "mois": 0}] * 2
    debutant = score_candidate(offre(), cand(items=projets), sims(2, 0.7, 0.7))
    assert debutant.detail["criteres"]["experience_projets"]["elements"]["debutant"] is True
    assert debutant.detail["criteres"]["experience_projets"]["note"] >= 50  # 0,6 × 100 sur les projets
    senior = score_candidate(offre(), cand(items=[{"genre": "experience", "titre": "Développeur", "texte": "api", "mois": 24}]), sims(1, 0.8, 0.8))
    assert senior.detail["criteres"]["experience_projets"]["elements"]["debutant"] is False
    irrelevant = score_candidate(offre(), cand(items=[{"genre": "experience", "titre": "Vendeur", "texte": "vente", "mois": 24}]), sims(1, 0.0, 0.0))
    assert irrelevant.detail["criteres"]["experience_projets"]["note"] == 0


# ---------------------------------------------------------------- critère 4 : spécialité
def test_specialite_conforme_partielle_inconnue_non_demandee():
    off = offre(specialites_ids={1}, specialites_noms=["Informatique"])
    assert score_candidate(off, cand(), sims()).detail["criteres"]["specialite"]["note"] == 100
    assert score_candidate(off, cand(mention_id=2, mention_nom="Gestion"), sims()).detail["criteres"]["specialite"]["note"] == 0
    part = score_candidate(off, cand(mention_id=2, mention_nom="Gestion", formations_texte="Licence en informatique de gestion"), sims())
    assert part.detail["criteres"]["specialite"]["note"] == 60 and part.detail["criteres"]["specialite"]["statut"] == "partiel"
    inc = score_candidate(off, cand(mention_id=None, mention_nom=None), sims())
    assert inc.detail["criteres"]["specialite"]["statut"] == "inconnu" and inc.detail["criteres"]["specialite"]["note"] == NOTE_INCONNU
    nd = score_candidate(offre(), cand(mention_id=2, mention_nom="Gestion"), sims()).detail["criteres"]["specialite"]
    assert nd["statut"] == "non_demande" and nd["note"] == 100


# ---------------------------------------------------------------- critère 5 : niveau d'études (obligatoire ≠ préférence)
def test_niveau_preference_vs_exigence_obligatoire():
    pref = offre(niveau_min_rang=5, niveau_min_nom="M2", niveau_obligatoire=False)
    oblig = offre(niveau_min_rang=5, niveau_min_nom="M2", niveau_obligatoire=True)
    c = cand(niveau_rang=4, niveau_nom="M1")
    rp, ro = score_candidate(pref, c, sims()), score_candidate(oblig, c, sims())
    assert rp.detail["criteres"]["niveau_etudes"]["note"] == ro.detail["criteres"]["niveau_etudes"]["note"] == 60  # même note…
    assert not rp.elimine and rp.detail["eligibilite"] == "conforme" and "simple préférence" in " ".join(rp.detail["points_a_verifier"])
    assert ro.elimine and ro.detail["eligibilite"] == "elimine" and "éliminatoire" in ro.detail["exigences_non_respectees"][0]  # … mais règle différente
    assert ro.score == rp.score  # le score reste calculé et visible : l'administrateur décide
    assert not score_candidate(oblig, cand(niveau_rang=5, niveau_nom="M2"), sims()).elimine


def test_niveau_inconnu_n_est_pas_un_echec():
    oblig = offre(niveau_min_rang=4, niveau_min_nom="M1", niveau_obligatoire=True)
    r = score_candidate(oblig, cand(niveau_rang=None, niveau_nom=None), sims())
    b = r.detail["criteres"]["niveau_etudes"]
    assert b["statut"] == "inconnu" and b["note"] == NOTE_INCONNU and not r.elimine and r.detail["eligibilite"] == "a_verifier"
    assert "Niveau d'études non renseigné." in r.detail["informations_manquantes"] and r.detail["fiabilite"] < 100


def test_competence_obligatoire_absente_marque_elimine_sans_changer_le_score():
    crit = [{"competence": "Python", "poids": 5, "niveau_requis": "avance", "obligatoire": True}]
    r = score_candidate(offre(criteres=crit), cand(competences=[{"nom": "Excel", "niveau": "expert", "source": "declaree"}]), sims())
    assert r.elimine and "Python" in r.detail["exigences_non_respectees"][0]
    sans = score_candidate(offre(criteres=[{**crit[0], "obligatoire": False}]), cand(competences=[{"nom": "Excel", "niveau": "expert", "source": "declaree"}]), sims())
    assert r.score == sans.score  # pas de pénalité cachée : seule la règle d'éligibilité change


# ---------------------------------------------------------------- critère 6 : disponibilité
def test_disponibilite_confirmee_inconnue_et_non_demandee():
    off = offre(periode_debut=date(2026, 12, 1), periode_fin=date(2027, 5, 31))
    d = lambda **kw: score_candidate(off, cand(**kw), sims()).detail["criteres"]["disponibilite"]
    assert d(dispo_debut=date(2026, 11, 1), dispo_fin=date(2027, 6, 30))["note"] == 100
    assert d(dispo_debut=date(2026, 12, 20), dispo_fin=date(2027, 6, 30))["note"] == 70
    assert d(dispo_debut=date(2027, 6, 1), dispo_fin=date(2027, 9, 1))["note"] == 0
    assert d(dispo_debut=date(2026, 1, 1), dispo_fin=date(2026, 6, 1))["note"] == 0
    inconnue = d()
    assert inconnue["statut"] == "inconnu" and inconnue["note"] == NOTE_INCONNU  # jamais 0 par défaut
    assert d(disponible=False)["note"] == 0
    assert d(dispo_type="emploi", dispo_debut=date(2026, 11, 1), dispo_fin=date(2027, 6, 30))["note"] < 50
    nd = score_candidate(offre(), cand(), sims()).detail["criteres"]["disponibilite"]
    assert nd["statut"] == "non_demande" and nd["note"] == 100


# ---------------------------------------------------------------- non invention + classement + justifications (plusieurs CV / offres)
def test_aucune_information_inventee():
    r = score_candidate(offre(), cand(competences=[], items=[], mention_id=None, niveau_rang=None), ItemSims())
    assert r.detail["criteres"]["competences"]["elements"]["trouvees"] == [] and r.detail["points_forts"] == [] or all("Disponible" in f or "conforme" in f for f in r.detail["points_forts"])
    assert "Aucune compétence renseignée." in r.detail["informations_manquantes"]


PROFILS = {
    "backend": cand(1, competences=[{"nom": "Python", "niveau": "expert", "source": "declaree"}, {"nom": "FastAPI", "niveau": "avance", "source": "declaree"}],
                    items=[{"genre": "experience", "titre": "Stagiaire développeur backend", "texte": "conception api interne recommandation plateforme", "mois": 8},
                           {"genre": "projet", "type": "personnel", "titre": "Moteur de recommandation", "texte": "moteur recommandation candidats", "mois": 0}]),
    "front": cand(2, competences=[{"nom": "React", "niveau": "avance", "source": "declaree"}, {"nom": "JavaScript", "niveau": "avance", "source": "declaree"}],
                  items=[{"genre": "experience", "titre": "Stagiaire front-end", "texte": "interfaces web composants", "mois": 6}]),
    "compta": cand(3, competences=[{"nom": "Comptabilité", "niveau": "avance", "source": "declaree"}, {"nom": "Excel", "niveau": "expert", "source": "declaree"}],
                   items=[{"genre": "experience", "titre": "Stagiaire comptabilité", "texte": "saisie comptable rapprochements bancaires", "mois": 6}], mention_id=2, mention_nom="Gestion"),
    "vide": cand(4, competences=[], items=[]),
}
OFFRES = {
    "backend": offre(id=10),
    "compta": offre(id=11, titre="Assistant comptable", missions="Saisie des écritures comptables, rapprochements bancaires et suivi des factures fournisseurs.",
                    criteres=[{"competence": "Comptabilité", "poids": 5, "niveau_requis": "intermediaire", "obligatoire": True}, {"competence": "Excel", "poids": 2, "niveau_requis": "intermediaire", "obligatoire": False}],
                    specialites_ids={2}, specialites_noms=["Gestion"]),
}


@pytest.mark.parametrize("nom_offre,attendu_premier", [("backend", 1), ("compta", 3)])
def test_classement_et_justifications_sur_profils_differents(nom_offre, attendu_premier):
    res = rank_candidates(OFFRES[nom_offre], list(PROFILS.values()), TfidfEngine())
    assert res[0][1].etudiant_id == attendu_premier and [r for r, _ in res] == [1, 2, 3, 4]
    premier = res[0][1].detail
    assert premier["points_forts"] and premier["criteres"]["competences"]["resume"] and premier["version_algorithme"] == VERSION_ALGORITHME
    dernier = res[-1][1]
    assert dernier.score < res[0][1].score and dernier.detail["informations_manquantes"]
    # les candidats conformes passent avant les éliminés, quel que soit le score
    elimines = [r.elimine for _, r in res]
    assert elimines == sorted(elimines)


def test_aucun_double_comptage_competence_masquee_pour_les_missions():
    """Une offre dont les missions ne citent que des compétences du référentiel ne doit pas faire monter le critère 2 par simple recoupement de mots-clés."""
    off = offre(missions="Python FastAPI Docker PostgreSQL Git")
    r = rank_candidates(off, [cand(1, items=[{"genre": "experience", "titre": "Dev", "texte": "", "mois": 6}])], TfidfEngine())[0][1]
    assert r.detail["criteres"]["missions"]["note"] <= 10
