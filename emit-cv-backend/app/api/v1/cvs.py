"""Gestion des CV : création/modification en ligne, import PDF/DOCX, publication, téléchargement du fichier."""
from fastapi import APIRouter, BackgroundTasks, Depends, File, HTTPException, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core import storage
from app.core.deps import get_current_user, require_etudiant
from app.db.session import get_db
from app.models import CV, Candidature, Etudiant, ModelCV, STATUT_RECOMMANDEE, Utilisateur, utcnow
from app.schemas.cv import CVIn, CVOut, CVResume
from app.services import cv_service
from app.services.journal import journaliser
from app.services import taches

router = APIRouter(prefix="/cvs", tags=["CV"])


def _cv_du_proprietaire(db: Session, cv_id: int, etu: Etudiant) -> CV:
    cv = db.get(CV, cv_id)
    if cv is None or cv.etudiant_id != etu.id:  # 404 aussi si le CV appartient à un autre : on ne révèle rien
        raise HTTPException(404, "CV introuvable.")
    return cv


def _verifier_modele(db: Session, model_cv_id: int | None) -> None:
    if model_cv_id and not db.get(ModelCV, model_cv_id):
        raise HTTPException(422, "Modèle de CV inconnu.")


@router.get("", response_model=list[CVResume], summary="Mes CV")
def mes_cvs(etu: Etudiant = Depends(require_etudiant), db: Session = Depends(get_db)):
    cvs = sorted(db.scalars(select(CV).where(CV.etudiant_id == etu.id)), key=lambda c: c.date_maj, reverse=True)
    return [cv_service.to_resume(c) for c in cvs]


@router.post("", response_model=CVOut, status_code=201, summary="Créer un CV en ligne")
def creer(data: CVIn, bg: BackgroundTasks, etu: Etudiant = Depends(require_etudiant), db: Session = Depends(get_db)):
    _verifier_modele(db, data.model_cv_id)
    if len(etu.cvs) >= 5:
        raise HTTPException(409, "Nombre maximal de CV atteint (5). Supprimez-en un avant d'en créer un autre.")
    cv = CV(etudiant_id=etu.id, titre=data.titre, model_cv_id=data.model_cv_id or cv_service.modele_par_defaut(db))
    cv_service.appliquer(db, cv, data)
    db.add(cv)
    journaliser(db, etu.id, f"Création du CV « {cv.titre} »")
    db.commit()
    db.refresh(cv)
    taches.enqueue(db, "analyse_cv", cv.id, "creation", priorite=4)
    bg.add_task(taches.declencher_inline)
    return cv_service.to_out(cv)


@router.post("/import", response_model=CVOut, status_code=201, summary="Importer un CV (PDF/DOCX) et le pré-remplir")
async def importer(bg: BackgroundTasks, file: UploadFile = File(...), etu: Etudiant = Depends(require_etudiant), db: Session = Depends(get_db)):
    if len(etu.cvs) >= 5:
        raise HTTPException(409, "Nombre maximal de CV atteint (5).")
    cv = await cv_service.importer_fichier(db, etu, file)
    journaliser(db, etu.id, f"Import du CV « {cv.titre} »")
    db.commit()
    taches.enqueue(db, "analyse_cv", cv.id, "import", priorite=4)
    bg.add_task(taches.declencher_inline)
    return cv_service.to_out(cv)


@router.get("/{cv_id}", response_model=CVOut, summary="Détail d'un CV (propriétaire, ou admin si publié)")
def detail(cv_id: int, user: Utilisateur = Depends(get_current_user), db: Session = Depends(get_db)):
    cv = db.get(CV, cv_id)
    if cv is None:
        raise HTTPException(404, "CV introuvable.")
    if user.role == "etudiant" and cv.etudiant_id != user.id:
        raise HTTPException(404, "CV introuvable.")
    if user.role == "admin" and cv.statut != "publie":
        raise HTTPException(403, "Ce CV n'est pas publié.")
    return cv_service.to_out(cv)


@router.put("/{cv_id}", response_model=CVOut, summary="Modifier un CV")
def modifier(cv_id: int, data: CVIn, bg: BackgroundTasks, etu: Etudiant = Depends(require_etudiant), db: Session = Depends(get_db)):
    cv = _cv_du_proprietaire(db, cv_id, etu)
    _verifier_modele(db, data.model_cv_id)
    cv_service.appliquer(db, cv, data)
    journaliser(db, etu.id, f"Modification du CV « {cv.titre} »")
    db.commit()
    db.refresh(cv)
    taches.enqueue(db, "analyse_cv", cv.id, "modification", priorite=4)  # le recalcul des classements suit si le contenu a changé
    bg.add_task(taches.declencher_inline)
    return cv_service.to_out(cv)


@router.post("/{cv_id}/publier", response_model=CVOut, summary="Publier un CV (visible de l'EMIT, inclus dans le matching)")
def publier(cv_id: int, bg: BackgroundTasks, etu: Etudiant = Depends(require_etudiant), db: Session = Depends(get_db)):
    cv = _cv_du_proprietaire(db, cv_id, etu)
    if cv.calculer_completude() < 50 or not cv.competences or not cv.formations:
        raise HTTPException(422, "CV trop incomplet pour être publié : ajoutez au moins une compétence, une formation et un résumé.")
    cv.statut, cv.est_public, cv.date_maj = "publie", True, utcnow()
    journaliser(db, etu.id, f"Publication du CV « {cv.titre} »")
    db.commit()
    db.refresh(cv)
    taches.enqueue(db, "analyse_cv", cv.id, "publication", priorite=3)
    taches.enqueue_recalcul_offres_ouvertes(db, "publication-cv")
    bg.add_task(taches.declencher_inline)
    return cv_service.to_out(cv)


@router.post("/{cv_id}/depublier", response_model=CVOut, summary="Retirer un CV de la publication")
def depublier(cv_id: int, bg: BackgroundTasks, etu: Etudiant = Depends(require_etudiant), db: Session = Depends(get_db)):
    cv = _cv_du_proprietaire(db, cv_id, etu)
    cv.statut, cv.est_public, cv.date_maj = "brouillon", False, utcnow()
    journaliser(db, etu.id, f"Dépublication du CV « {cv.titre} »")
    db.commit()
    db.refresh(cv)
    taches.enqueue_recalcul_offres_ouvertes(db, "depublication-cv")
    bg.add_task(taches.declencher_inline)
    return cv_service.to_out(cv)


@router.delete("/{cv_id}", status_code=204, summary="Supprimer un CV")
def supprimer(cv_id: int, bg: BackgroundTasks, etu: Etudiant = Depends(require_etudiant), db: Session = Depends(get_db)):
    cv = _cv_du_proprietaire(db, cv_id, etu)
    etait_publie = cv.statut == "publie"
    # Les simples recommandations de l'IA disparaissent avec le CV ; une vraie candidature l'en empêche.
    for cand in db.scalars(select(Candidature).where(Candidature.cv_id == cv.id)):
        if cand.statut != STATUT_RECOMMANDEE:
            raise HTTPException(409, "Ce CV est utilisé dans une candidature : il ne peut pas être supprimé.")
        db.delete(cand)
    db.flush()
    storage.delete("cv", cv.fichier_pdf)
    journaliser(db, etu.id, f"Suppression du CV « {cv.titre} »")
    db.delete(cv)
    db.commit()
    if etait_publie:
        taches.enqueue_recalcul_offres_ouvertes(db, "suppression-cv")
        bg.add_task(taches.declencher_inline)


@router.get("/{cv_id}/fichier", summary="Télécharger le fichier importé (propriétaire, ou admin si publié)")
def fichier(cv_id: int, user: Utilisateur = Depends(get_current_user), db: Session = Depends(get_db)):
    cv = db.get(CV, cv_id)
    if cv is None or not cv.fichier_pdf:
        raise HTTPException(404, "Aucun fichier pour ce CV.")
    if user.role == "etudiant" and cv.etudiant_id != user.id:
        raise HTTPException(404, "Aucun fichier pour ce CV.")
    if user.role == "admin" and cv.statut != "publie":
        raise HTTPException(403, "Ce CV n'est pas publié.")
    path = storage.path_of("cv", cv.fichier_pdf)
    if not path:
        raise HTTPException(404, "Fichier introuvable sur le serveur.")
    media = "application/pdf" if path.suffix == ".pdf" else "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    return FileResponse(path, media_type=media, filename=cv.fichier_nom_origine or path.name)
