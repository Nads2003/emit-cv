"""Tests unitaires du module IA (sans base de données) : référentiel, similarité, extraction, parseur, caractéristiques."""
from datetime import date

from app.ai import features
from app.ai.embeddings import TfidfEngine
from app.ai.parser import parse_cv_text
from app.ai.skills_taxonomy import canonical, canonical_key, extract_skills, mask_skills


def test_taxonomie_synonymes_et_accents():
    assert canonical("postgres") == "PostgreSQL" and canonical("cybersecurite") == "Cybersécurité"
    assert canonical_key("ReactJS") == canonical_key("react js")
    assert canonical("CompétenceInconnue") == "CompétenceInconnue"


def test_extraction_competences_sans_faux_positifs():
    s = extract_skills("Développeur React Native et Java. Notions de C++ et C#. J'aime la javascript.")
    assert "React Native" in s and "React" not in s
    assert {"Java", "C++", "C#", "JavaScript"} <= set(s)
    assert "R" not in extract_skills("Je travaille sur un projet réseau")


def test_masquage_des_competences():
    m = mask_skills("Développer une API avec Python et PostgreSQL pour la gestion de stock")
    assert "python" not in m and "postgresql" not in m  # compétences retirées (déjà notées au critère 1)
    assert "developper" in m and "pour" in m  # les autres mots restent


def test_tfidf_similarite_locale_et_par_corpus():
    e = TfidfEngine()
    sims = e.similarities("développeur python api backend", ["python api backend fastapi", "comptabilité excel gestion", ""])
    assert sims[0] > sims[1] and sims[2] == 0.0 and all(0 <= s <= 1 for s in sims)
    assert e.similarities("", ["a b"]) == [0.0] and e.similarities("x", []) == []
    e2 = TfidfEngine()
    e2.fit_corpus(iter(["python api backend", "comptabilité excel", "api rest python flask", "marketing réseaux sociaux"]))  # flux
    s2 = e2.similarities("api python", ["python api backend", "marketing réseaux sociaux"])
    assert s2[0] > s2[1]
    TfidfEngine().fit_corpus(iter([]))  # corpus vide : pas d'exception


def test_caracteristiques_sources_et_cache_par_hash():
    cv = {"titre": "Dev", "resume": "Je connais Docker et Git.", "texte_extrait": "",
          "competences": [{"nom": "postgres", "niveau_maitrise": "avance"}], "formations": [{"diplome": "Master 1", "etablissement": "EMIT", "annee": 2025}],
          "experiences": [{"poste": "Stagiaire", "entreprise": "ACME", "date_debut": date(2024, 1, 1), "date_fin": date(2024, 7, 1), "description": "API en Python"}],
          "projets": [{"titre": "Site e-commerce", "description": "React", "type": "personnel", "annee": 2024}]}
    f = features.construire(cv)
    src = {c["nom"]: c["source"] for c in f["caracteristiques"]["competences"]}
    assert src["PostgreSQL"] == "declaree" and src["Docker"] == "texte" and src["Python"] == "texte" and src["React"] == "texte"
    assert [i["genre"] for i in f["caracteristiques"]["items"]] == ["experience", "projet"] and f["caracteristiques"]["items"][0]["mois"] == 6
    assert features.construire(cv)["hash_contenu"] == f["hash_contenu"]  # déterministe -> cache valide
    cv["resume"] += " Nouveau."
    assert features.construire(cv)["hash_contenu"] != f["hash_contenu"]  # modification -> réanalyse


def test_parseur_cv_complet():
    texte = """Fanja Razafy
Data scientist junior
PROFIL
Étudiante en Master 2 Informatique spécialisée en machine learning et NLP.
COMPÉTENCES
Python (expert), scikit-learn, Pandas, SQL (notions), Travail en équipe
FORMATION
Master 2 Informatique - EMIT - 2025
Baccalauréat série C - Lycée Andohalo - 2020
EXPÉRIENCES PROFESSIONNELLES
Stagiaire data - Telma - 03/2024 - 08/2024
Construction d'un modèle de scoring.
Assistant de recherche - Université - 2022 - Présent
PROJETS
Application de gestion de stock
Développement d'une application web de gestion pour une PME locale.
Contact : fanja@test.mg +261 34 12 345 67"""
    p = parse_cv_text(texte)
    niveaux = {c["nom"]: c["niveau_maitrise"] for c in p["competences"]}
    assert niveaux["Python"] == "expert" and niveaux["SQL"] == "debutant" and "scikit-learn" in niveaux and "Machine Learning" in niveaux
    assert len(p["formations"]) == 2 and p["formations"][0]["annee"] == 2025
    assert len(p["experiences"]) == 2 and p["experiences"][0]["description"].startswith("Construction")
    assert p["experiences"][0]["date_debut"] == date(2024, 3, 1) and p["experiences"][0]["date_fin"] == date(2024, 8, 1)
    assert p["experiences"][1]["date_fin"] is None
    assert len(p["projets"]) == 1 and p["projets"][0]["titre"] == "Application de gestion de stock"
    assert p["email_detecte"] == "fanja@test.mg" and "Master 2" in p["resume"]
