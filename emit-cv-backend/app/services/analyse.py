"""Analyse d'un CV : extraction différée du fichier, calcul des caractéristiques, mise en cache.

Le résultat est réutilisé tant que le contenu du CV (hash) et la version de l'extracteur n'ont pas changé :
consulter ou reclasser ne réanalyse jamais les documents."""
import logging

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.ai import features
from app.ai.extraction import FichierInvalide, extract_text_info
from app.ai.parser import parse_cv_text
from app.core import storage
from app.models import CV, Competence, CVAnalyse, Experience, Formation, Projet, formater_duree, utcnow

log = logging.getLogger("emit.analyse")


def contenu_cv(cv: CV) -> dict:
    return {
        "titre": cv.titre, "resume": cv.resume, "texte_extrait": cv.texte_extrait,
        "competences": [{"nom": c.nom, "niveau_maitrise": c.niveau_maitrise} for c in cv.competences],
        "formations": [{"diplome": f.diplome, "etablissement": f.etablissement, "annee": f.annee} for f in cv.formations],
        "experiences": [{"poste": e.poste, "entreprise": e.entreprise, "date_debut": e.date_debut, "date_fin": e.date_fin, "description": e.description} for e in cv.experiences],
        "projets": [{"titre": p.titre, "description": p.description, "type": p.type, "annee": p.annee} for p in cv.projets],
    }


def appliquer_extraction(cv: CV, data: bytes) -> tuple[str, str]:
    """Extrait le texte du fichier et PRÉ-REMPLIT le CV (brouillon). Retourne (etat, message). Lève FichierInvalide si refusé."""
    kind, texte, etat = extract_text_info(data)
    cv.texte_extrait = texte[:60000]
    if etat == "ocr_requis":
        return etat, "PDF scanné : le texte n'a pas pu être lu automatiquement (reconnaissance de caractères non disponible). Complétez votre CV manuellement."
    if etat == "vide":
        return etat, "Aucun texte exploitable dans ce fichier. Complétez votre CV manuellement."
    parsed = parse_cv_text(texte)
    if not cv.titre or cv.titre == "CV importé":
        cv.titre = parsed["titre"] if len(parsed["titre"]) >= 2 else "CV importé"
    cv.resume = parsed["resume"]
    cv.competences = [Competence(**c) for c in parsed["competences"][:40]]
    cv.formations = [Formation(**f) for f in parsed["formations"]]
    exps = []
    for e in parsed["experiences"]:
        exp = Experience(poste=e["poste"], entreprise=e["entreprise"], date_debut=e["date_debut"], date_fin=e["date_fin"], dure=formater_duree(e["date_debut"], e["date_fin"]))
        exp.description = e.get("description", "")
        exps.append(exp)
    cv.experiences = exps
    cv.projets = [Projet(**p) for p in parsed["projets"]]
    return "ok", ""


def analyser_cv(db: Session, cv_id: int, forcer: bool = False) -> dict:
    """Retourne {"statut", "change": bool (contenu modifié depuis la dernière analyse), "cache": bool}."""
    cv = db.scalar(select(CV).where(CV.id == cv_id).options(
        selectinload(CV.competences), selectinload(CV.formations), selectinload(CV.experiences).selectinload(Experience.infos),
        selectinload(CV.projets), selectinload(CV.infos), selectinload(CV.analyse)))
    if cv is None:
        return {"statut": "supprime", "change": False, "cache": False}
    a = cv.analyse or CVAnalyse(cv_id=cv.id)
    cv.analyse = a
    precedent = a.message or ""  # message de la dernière analyse (None pour un CV jamais analysé)
    a.statut, etat_ext, message = "en_cours", None, precedent
    # Extraction différée (importation en lot) : le fichier est lu ici, par le worker
    if cv.source == "importe" and cv.fichier_pdf and not cv.texte_extrait and not cv.competences:
        path = storage.path_of("cv", cv.fichier_pdf)
        if path is None:
            a.statut, a.message = "echec", "Fichier introuvable sur le serveur."
            db.commit()
            raise FileNotFoundError(a.message)
        try:
            etat_ext, message = appliquer_extraction(cv, path.read_bytes())
        except FichierInvalide as exc:
            a.statut, a.message = "echec", str(exc)  # refus définitif : inutile de réessayer
            db.commit()
            return {"statut": "echec", "change": False, "cache": False}
    elif precedent.startswith(("PDF scanné", "Aucun texte")):
        etat_ext = "ocr_requis" if precedent.startswith("PDF scanné") else "vide"
    feat = features.construire(contenu_cv(cv))
    carac = feat["caracteristiques"]
    contenu_vide = not carac["competences"] and not carac["items"]
    ancien_ok = a.hash_contenu == feat["hash_contenu"] and a.version_extracteur == feat["version"] and bool(a.texte_scoring or a.caracteristiques)
    if ancien_ok and not forcer and etat_ext is None:
        a.statut = "ok" if not contenu_vide else ("ocr_requis" if precedent.startswith("PDF scanné") else "vide" if precedent else "ok")
        db.commit()
        return {"statut": a.statut, "change": False, "cache": True}
    a.hash_contenu, a.version_extracteur = feat["hash_contenu"], feat["version"]
    a.texte_scoring, a.caracteristiques, a.analysee_le = feat["texte_scoring"], carac, utcnow()
    if contenu_vide and etat_ext in ("ocr_requis", "vide"):
        a.statut, a.message = etat_ext, message
    else:
        a.statut, a.message = "ok", ""
    cv.date_maj = utcnow() if etat_ext is not None else cv.date_maj
    db.commit()
    return {"statut": a.statut, "change": True, "cache": False}
