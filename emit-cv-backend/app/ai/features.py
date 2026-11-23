"""Caractéristiques d'un CV, calculées UNE fois puis mises en cache (table cv_analyse).

Fonction pure : à partir du contenu structuré du CV (+ texte extrait d'un fichier importé), produit
  - les compétences avec leur source : « declaree » (saisie/validée par l'étudiant) ou « texte » (détectée dans le CV) ;
  - les éléments d'expérience et de projets (titre, contexte, texte des missions, durée) ;
  - un hash du contenu : si le hash et la version sont inchangés, l'analyse n'est pas refaite.
Rien n'est inventé : tout provient du CV.
"""
import hashlib
import json
from datetime import date

from app.ai.skills_taxonomy import canonical, extract_skills, mask_skills

VERSION_EXTRACTEUR = "2.0"


def _mois(debut: date | None, fin: date | None) -> int:
    if not debut:
        return 0
    fin = fin or date.today()
    return max(0, (fin.year - debut.year) * 12 + (fin.month - debut.month))


def construire(cv: dict) -> dict:
    """cv = {titre, resume, texte_extrait, competences:[{nom,niveau_maitrise}], formations:[{diplome,etablissement,annee}],
             experiences:[{poste,entreprise,date_debut,date_fin,description}], projets:[{titre,description,type,annee}]}"""
    declarees = {}
    for c in cv.get("competences", []):
        declarees[canonical(c["nom"])] = c.get("niveau_maitrise") or "intermediaire"
    # compétences retrouvées dans le texte (résumé, missions, projets, fichier importé) mais non déclarées
    corps = " \n".join([cv.get("resume", ""), cv.get("texte_extrait", "")]
                       + [f"{e['poste']} {e.get('description', '')}" for e in cv.get("experiences", [])]
                       + [f"{p['titre']} {p.get('description', '')}" for p in cv.get("projets", [])])
    competences = [{"nom": n, "niveau": lvl, "source": "declaree"} for n, lvl in declarees.items()]
    competences += [{"nom": n, "niveau": None, "source": "texte"} for n in extract_skills(corps) if n not in declarees]

    items = []
    for e in cv.get("experiences", []):
        ctx = f"{e['poste']} {e.get('entreprise', '')}".strip()
        items.append({"genre": "experience", "titre": ctx, "mois": _mois(e.get("date_debut"), e.get("date_fin")),
                      "texte": mask_skills(f"{e['poste']} {e.get('description', '')}")})
    for p in cv.get("projets", []):
        items.append({"genre": "projet", "type": p.get("type", "academique"), "titre": p["titre"], "mois": 0,
                      "texte": mask_skills(f"{p['titre']} {p.get('description', '')}")})

    formations_texte = " ".join(f"{f['diplome']} {f.get('etablissement', '')}" for f in cv.get("formations", []))
    caracteristiques = {"competences": competences, "items": items, "formations_texte": formations_texte,
                        "a_experiences": any(i["genre"] == "experience" for i in items), "a_projets": any(i["genre"] == "projet" for i in items)}
    texte_scoring = " ".join([cv.get("titre", ""), " ".join(i["texte"] for i in items)]).strip()
    contenu = json.dumps({"c": caracteristiques, "t": cv.get("titre", ""), "r": cv.get("resume", "")}, sort_keys=True, default=str)
    return {"caracteristiques": caracteristiques, "texte_scoring": texte_scoring,
            "hash_contenu": hashlib.sha256(contenu.encode()).hexdigest(), "version": VERSION_EXTRACTEUR}
