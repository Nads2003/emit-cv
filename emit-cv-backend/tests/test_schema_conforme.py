"""Conformité du schéma de base de données avec le DIAGRAMME DE CLASSES du cahier des charges.

Pour chacune des 17 classes : le nom de table et TOUS les attributs du diagramme existent avec le même nom (en minuscules, convention SQL),
et la table ne contient AUCUNE autre colonne que sa clé primaire et ses clés étrangères. Tout ajout hors diagramme vit dans des tables
« complémentaires » séparées, listées explicitement ci-dessous."""
from sqlalchemy import inspect

from app.db.session import engine

# classe du diagramme -> attributs du diagramme (noms conservés ; « scrore » et « dure » sont ceux du diagramme)
DIAGRAMME = {
    "utilisateur": {"id", "nom", "email", "mdp", "role"},
    "historique": {"id", "action", "date"},
    "notification": {"id", "message", "date", "lu"},
    "critereoffre": {"id", "poids", "niveaurequis", "obligatoire"},
    "offre": {"id", "titre", "description", "datecreation", "statut"},
    "candidature": {"id", "date", "statut"},
    "mention": {"nom"},
    "niveauetude": {"nom"},
    "etudiant": {"matricule"},
    "administrateur": {"poste"},
    "profile": {"id", "photo", "telephone", "adresse"},
    "cv": {"id", "titre", "datecreation", "statut", "source", "fichierpdf", "estpublic"},
    "modelcv": {"id", "nom", "description", "apercu"},
    "recommandation": {"id", "scrore", "statut", "date"},
    "competence": {"id", "nom", "niveaumaitrise"},
    "formation": {"id", "diplome", "etablissement", "annee"},
    "experience": {"id", "poste", "entreprise", "dure", "datedebut", "datefin"},
}
# associations du diagramme -> (table, colonne FK, table référencée)
RELATIONS = [
    ("historique", "utilisateur_id", "utilisateur"), ("notification", "utilisateur_id", "utilisateur"),
    ("etudiant", "id", "utilisateur"), ("administrateur", "id", "utilisateur"),
    ("etudiant", "mention_id", "mention"), ("niveauetude", "mention_id", "mention"),
    ("profile", "etudiant_id", "etudiant"), ("cv", "etudiant_id", "etudiant"), ("cv", "modelcv_id", "modelcv"),
    ("offre", "administrateur_id", "administrateur"), ("critereoffre", "offre_id", "offre"), ("critereoffre", "competence_id", "competence"),
    ("candidature", "offre_id", "offre"), ("candidature", "cv_id", "cv"), ("recommandation", "candidature_id", "candidature"),
    ("competence", "cv_id", "cv"), ("formation", "cv_id", "cv"), ("experience", "cv_id", "cv"),
    ("viser", "offre_id", "offre"), ("viser", "mention_id", "mention"),  # Mention 0..* — viser — Offre 0..*
]
COMPLEMENTS = {"disponibilite", "etudiant_niveau", "cv_infos", "experience_infos", "projet", "cv_analyse", "offre_infos", "scoring_run", "recommandation_detail",
               "tache", "etudiant_autorise", "import_liste", "import_ligne", "inscription_en_attente", "limite_debit"}


def test_les_17_classes_et_leurs_attributs_sont_presents_sans_colonne_en_trop():
    insp = inspect(engine)
    tables = set(insp.get_table_names())
    for table, attributs in DIAGRAMME.items():
        assert table in tables, f"table manquante : {table}"
        colonnes = {c["name"] for c in insp.get_columns(table)}
        assert attributs <= colonnes, f"{table} : attributs du diagramme manquants {attributs - colonnes}"
        en_trop = {c for c in colonnes - attributs if c != "id" and not c.endswith("_id")}
        assert not en_trop, f"{table} : colonnes hors diagramme {en_trop}"


def test_associations_du_diagramme_sont_des_cles_etrangeres():
    insp = inspect(engine)
    for table, colonne, cible in RELATIONS:
        fks = {(tuple(fk["constrained_columns"]), fk["referred_table"]) for fk in insp.get_foreign_keys(table)}
        assert ((colonne,), cible) in fks, f"{table}.{colonne} -> {cible} absente"


def test_aucune_table_inattendue():
    attendues = set(DIAGRAMME) | {"viser"} | COMPLEMENTS
    reelles = set(inspect(engine).get_table_names())
    assert reelles == attendues, f"écart : en trop {reelles - attendues}, manquantes {attendues - reelles}"


def test_unicites_et_obligations_du_diagramme():
    insp = inspect(engine)
    uniques = lambda t: {tuple(u["column_names"]) for u in insp.get_unique_constraints(t)} | {tuple(i["column_names"]) for i in insp.get_indexes(t) if i.get("unique")}
    assert ("email",) in uniques("utilisateur") and ("matricule",) in uniques("etudiant")
    assert ("etudiant_id",) in uniques("profile")  # Etudiant 1 — 1 Profile
    nullable = lambda t, c: next(x["nullable"] for x in insp.get_columns(t) if x["name"] == c)
    assert not nullable("cv", "modelcv_id") and not nullable("etudiant", "mention_id") and not nullable("candidature", "cv_id")
    assert not nullable("historique", "utilisateur_id") and not nullable("critereoffre", "competence_id")
