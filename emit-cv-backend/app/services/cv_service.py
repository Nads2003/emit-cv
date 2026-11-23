"""Logique métier des CV : (dé)sérialisation, canonisation des compétences, import de fichier."""
from fastapi import HTTPException, UploadFile
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.ai.extraction import FichierInvalide, extract_text_info, valider_securite, detect_type
from app.ai.skills_taxonomy import canonical
from app.core import storage
from app.core.config import settings
from app.models import CV, CVAnalyse, Competence, Etudiant, Experience, Formation, ModelCV, Projet, formater_duree, utcnow
from app.services import analyse as analyse_service
from app.schemas.cv import CVIn, CVOut, CVResume


def to_out(cv: CV) -> CVOut:
    out = CVOut.model_validate(cv)
    out.a_fichier = bool(cv.fichier_pdf)
    out.completude = cv.calculer_completude()
    for e_out, e in zip(out.experiences, cv.experiences):
        e_out.duree_mois = e.calculer_duree_mois()
    return out


def to_resume(cv: CV) -> CVResume:
    return CVResume(id=cv.id, titre=cv.titre, statut=cv.statut, source=cv.source, completude=cv.calculer_completude(),
                    date_maj=cv.date_maj, nb_competences=len(cv.competences))


def modele_par_defaut(db: Session) -> int:
    return db.scalar(select(ModelCV.id).order_by(ModelCV.id).limit(1))


def appliquer(db: Session, cv: CV, data: CVIn) -> None:
    """Applique un CVIn sur un CV (remplace les listes). Les compétences sont ramenées à leur nom canonique."""
    cv.titre, cv.resume = data.titre.strip(), data.resume.strip()
    cv.model_cv_id = data.model_cv_id or cv.model_cv_id or modele_par_defaut(db)
    cv.date_maj = utcnow()
    cv.competences.clear()
    vues = set()
    for c in data.competences:
        nom = canonical(c.nom)
        if nom.lower() in vues:
            continue
        vues.add(nom.lower())
        cv.competences.append(Competence(nom=nom, niveau_maitrise=c.niveau_maitrise))
    cv.formations.clear()
    cv.formations.extend(Formation(**f.model_dump()) for f in data.formations)
    cv.experiences.clear()
    cv.experiences.clear()
    for e in data.experiences:
        d = e.model_dump(exclude={"description"})
        exp = Experience(**d, dure=formater_duree(e.date_debut, e.date_fin))
        exp.description = e.description
        cv.experiences.append(exp)
    cv.projets.clear()
    cv.projets.extend(Projet(**p.model_dump()) for p in data.projets)


def creer_cv_depuis_octets(db: Session, etudiant: Etudiant, data: bytes, nom_fichier: str, differe: bool = False) -> CV:
    """Valide (type réel, contenu actif, bombes de décompression), stocke le fichier puis crée un CV *brouillon*.
    differe=False : extraction immédiate (téléversement interactif) ; differe=True : extraction faite plus tard par un worker (import en lot)."""
    limite = settings.max_cv_mb * 1024 * 1024
    if len(data) > limite:
        raise HTTPException(413, f"Fichier trop volumineux (maximum {settings.max_cv_mb} Mo).")
    try:
        kind = detect_type(data)
        valider_securite(data, kind)
    except FichierInvalide as exc:
        raise HTTPException(422, str(exc))
    cv = CV(etudiant_id=etudiant.id, titre="CV importé", source="importe", statut="brouillon", est_public=False,
            model_cv_id=modele_par_defaut(db), fichier_nom_origine=(nom_fichier or "cv")[:255])
    if not differe:
        try:
            etat, message = analyse_service.appliquer_extraction(cv, data)
        except FichierInvalide as exc:
            raise HTTPException(422, str(exc))
        cv.analyse = CVAnalyse(statut=etat if etat != "ok" else "en_attente", message=message)
    else:
        cv.analyse = CVAnalyse(statut="en_attente")
    cv.fichier_pdf = storage.save_bytes("cv", kind, data)
    db.add(cv)
    db.commit()
    db.refresh(cv)
    return cv


async def importer_fichier(db: Session, etudiant: Etudiant, upload: UploadFile, differe: bool = False) -> CV:
    limite = settings.max_cv_mb * 1024 * 1024
    data = await upload.read(limite + 1)
    return creer_cv_depuis_octets(db, etudiant, data, upload.filename or "cv", differe)
