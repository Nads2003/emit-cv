"""Génère database/tables.sql (PostgreSQL) à partir des modèles : une seule source de vérité, jamais désynchronisée.

    python -m scripts.export_sql"""
from pathlib import Path

from sqlalchemy.dialects import postgresql
from sqlalchemy.schema import CreateIndex, CreateTable

from app import models  # noqa: F401
from app.db.base import Base

SORTIE = Path(__file__).resolve().parents[2] / "database" / "tables.sql"
CLASSES = {  # table -> classe du diagramme de classes du cahier des charges
    "utilisateur": "Utilisateur", "etudiant": "Etudiant", "administrateur": "Administrateur", "profile": "Profile", "mention": "Mention",
    "niveauetude": "NiveauEtude", "cv": "CV", "modelcv": "ModelCV", "competence": "Competence", "formation": "Formation", "experience": "Experience",
    "offre": "Offre", "critereoffre": "CritereOffre", "candidature": "Candidature", "recommandation": "Recommandation",
    "notification": "Notification", "historique": "Historique", "viser": "association « viser » (Mention 0..* — Offre 0..*)",
}
COMPLEMENTS = {
    "disponibilite": "Disponibilité de l'étudiant (cahier des charges, section 4 : « Ajouter sa disponibilité »)",
    "etudiant_niveau": "Niveau d'études de l'étudiant (le diagramme relie NiveauEtude à Mention, pas à Etudiant)",
    "cv_infos": "Résumé, texte extrait du fichier importé, nom d'origine, date de mise à jour du CV",
    "experience_infos": "Missions et réalisations d'une expérience (critère d'IA « Adéquation aux missions »)",
    "projet": "Projets académiques et personnels (critère d'IA « Expérience et projets »)",
    "cv_analyse": "Résultat mis en cache de l'analyse d'un CV (statut : en_attente, en_cours, ok, ocr_requis, vide, echec)",
    "offre_infos": "Type d'opportunité, échéances, niveau d'études minimal et son caractère obligatoire",
    "scoring_run": "Traçabilité de chaque classement : version de l'algorithme, pondérations, critères de l'offre",
    "recommandation_detail": "Rang, détail explicable du score, statut éliminatoire et calcul d'origine",
    "tache": "File de tâches asynchrones (analyses de CV, calculs de classement) avec suivi d'état",
    "etudiant_autorise": "Liste officielle des étudiants autorisés à créer un compte (e-mail et matricule uniques)",
    "import_liste": "Imports Excel de la liste officielle (aperçu puis confirmation)",
    "import_ligne": "Lignes d'un import Excel et leur diagnostic",
    "inscription_en_attente": "Inscription en attente de vérification d'e-mail (aucun compte tant que non confirmée)",
    "limite_debit": "Compteurs de limitation de débit (anti brute-force) partagés entre workers",
}


def main() -> Path:
    d = postgresql.dialect()
    out = ["-- ============================================================================",
           "-- EMIT · CV intelligent : schéma PostgreSQL",
           "-- Généré automatiquement depuis les modèles (python -m scripts.export_sql). Ne pas modifier à la main.",
           "--",
           "-- 17 tables = les 17 classes du DIAGRAMME DE CLASSES du cahier des charges : mêmes noms de tables et de colonnes",
           "--   (en minuscules : PostgreSQL ignore la casse des identifiants non guillemetés). Seules colonnes ajoutées : clés primaires/étrangères.",
           "--   Noms conservés tels quels dans le diagramme : « scrore » (Recommandation) et « dure » (Experience).",
           "-- + l'association « viser » + des tables COMPLÉMENTAIRES, séparées, pour ce que le diagramme ne couvre pas.",
           "-- Mots de passe : la colonne utilisateur.mdp contient un HASH Argon2, jamais le mot de passe.",
           "-- ============================================================================", ""]
    for table in Base.metadata.sorted_tables:
        if table.name in CLASSES:
            out.append(f"-- Classe du diagramme : {CLASSES[table.name]}")
        else:
            out.append(f"-- COMPLÉMENT (hors diagramme) : {COMPLEMENTS[table.name]}")
        out.append(str(CreateTable(table).compile(dialect=d)).strip() + ";")
        for idx in sorted(table.indexes, key=lambda i: i.name):
            out.append(str(CreateIndex(idx).compile(dialect=d)).strip() + ";")
        out.append("")
    SORTIE.parent.mkdir(parents=True, exist_ok=True)
    SORTIE.write_text("\n".join(out), encoding="utf-8")
    return SORTIE


if __name__ == "__main__":
    print(main())
