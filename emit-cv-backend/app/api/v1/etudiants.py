"""Profil étudiant, disponibilité, photo, et recherche de profils (administrateur)."""
from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, selectinload

from app.ai.skills_taxonomy import canonical
from app.core import storage
from app.core.config import settings
from app.core.deps import get_current_user, require_admin, require_etudiant
from app.db.session import get_db
from app.models import CV, Administrateur, Competence, Disponibilite, Etudiant, EtudiantNiveau, Mention, NiveauEtude, Profile, Utilisateur
from app.schemas.etudiant import DisponibiliteIn, EtudiantMoiIn, EtudiantMoiOut, EtudiantPage, EtudiantResume
from app.services.journal import journaliser
from app.services.presenters import etudiant_moi, etudiant_resume
from app.services import taches

from fastapi import BackgroundTasks

router = APIRouter(prefix="/etudiants", tags=["Étudiants"])


@router.get("/moi", response_model=EtudiantMoiOut, summary="Mon profil")
def mon_profil(etu: Etudiant = Depends(require_etudiant)):
    return etudiant_moi(etu)


@router.put("/moi", response_model=EtudiantMoiOut, summary="Mettre à jour mon profil")
def maj_profil(data: EtudiantMoiIn, bg: BackgroundTasks, etu: Etudiant = Depends(require_etudiant), db: Session = Depends(get_db)):
    autre = db.scalar(select(Etudiant.id).where(Etudiant.matricule == data.matricule, Etudiant.id != etu.id))
    if autre:
        raise HTTPException(409, "Ce matricule est déjà utilisé.")
    if not db.get(Mention, data.mention_id):
        raise HTTPException(422, "Mention inconnue.")
    if data.niveau_id:
        niveau = db.get(NiveauEtude, data.niveau_id)
        if not niveau or niveau.mention_id != data.mention_id:
            raise HTTPException(422, "Niveau d'études invalide pour cette mention.")
    etu.nom, etu.matricule, etu.mention_id, etu.niveau_id = data.nom.strip(), data.matricule, data.mention_id, data.niveau_id
    if etu.profil is None:
        etu.profil = Profile()
    etu.profil.telephone, etu.profil.adresse = data.telephone, data.adresse
    journaliser(db, etu.id, "Mise à jour du profil")
    db.commit()
    db.refresh(etu)
    taches.enqueue_recalcul_offres_ouvertes(db, "profil")  # mention/niveau influencent le score
    bg.add_task(taches.declencher_inline)
    return etudiant_moi(etu)


@router.put("/moi/disponibilite", response_model=EtudiantMoiOut, summary="Définir ma disponibilité")
def maj_dispo(data: DisponibiliteIn, bg: BackgroundTasks, etu: Etudiant = Depends(require_etudiant), db: Session = Depends(get_db)):
    etu.disponible, etu.dispo_debut, etu.dispo_fin, etu.dispo_type = data.disponible, data.dispo_debut, data.dispo_fin, data.dispo_type
    journaliser(db, etu.id, "Mise à jour de la disponibilité")
    db.commit()
    db.refresh(etu)
    taches.enqueue_recalcul_offres_ouvertes(db, "disponibilite")
    bg.add_task(taches.declencher_inline)
    return etudiant_moi(etu)


@router.post("/moi/photo", status_code=204, summary="Envoyer ma photo de profil (JPEG/PNG, 2 Mo max)")
async def envoyer_photo(file: UploadFile = File(...), etu: Etudiant = Depends(require_etudiant), db: Session = Depends(get_db)):
    limite = settings.max_photo_mb * 1024 * 1024
    data = await file.read(limite + 1)
    if len(data) > limite:
        raise HTTPException(413, f"Image trop volumineuse (maximum {settings.max_photo_mb} Mo).")
    if data[:3] == b"\xff\xd8\xff":
        ext = "jpg"
    elif data[:8] == b"\x89PNG\r\n\x1a\n":
        ext = "png"
    else:
        raise HTTPException(422, "Format d'image non supporté (JPEG ou PNG uniquement).")
    if etu.profil is None:
        etu.profil = Profile()
    storage.delete("photos", etu.profil.photo)
    etu.profil.photo = storage.save_bytes("photos", ext, data)
    db.commit()


@router.get("/{etudiant_id}/photo", summary="Photo de profil (propriétaire ou administrateur)")
def photo(etudiant_id: int, user: Utilisateur = Depends(get_current_user), db: Session = Depends(get_db)):
    if user.role != "admin" and user.id != etudiant_id:
        raise HTTPException(403, "Accès refusé.")
    profil = db.scalar(select(Profile).where(Profile.etudiant_id == etudiant_id))
    path = storage.path_of("photos", profil.photo) if profil and profil.photo else None
    if not path:
        raise HTTPException(404, "Aucune photo.")
    return FileResponse(path, media_type="image/png" if path.suffix == ".png" else "image/jpeg", headers={"Cache-Control": "private, max-age=300"})


@router.get("", response_model=EtudiantPage, summary="Rechercher et filtrer les profils (admin)")
def rechercher(
    q: str | None = Query(None, max_length=100, description="Nom, matricule, titre de CV ou compétence"),
    competence: list[str] = Query(default=[], description="Compétences exigées (toutes)"),
    mention_id: int | None = None,
    niveau_id: int | None = None,
    disponible: bool | None = None,
    page: int = Query(1, ge=1),
    taille: int = Query(20, ge=1, le=100),
    _: Administrateur = Depends(require_admin),
    db: Session = Depends(get_db),
):
    # Seuls les étudiants ayant un CV publié sont consultables par l'EMIT
    cond = [Etudiant.cvs.any(CV.statut == "publie")]
    if q:
        like = f"%{q.strip()}%"
        cond.append(or_(Etudiant.nom.ilike(like), Etudiant.matricule.ilike(like),
                        Etudiant.cvs.any(CV.titre.ilike(like)), Etudiant.cvs.any(CV.competences.any(Competence.nom.ilike(like)))))
    for comp in competence:
        cond.append(Etudiant.cvs.any((CV.statut == "publie") & CV.competences.any(func.lower(Competence.nom) == canonical(comp).lower())))
    if mention_id:
        cond.append(Etudiant.mention_id == mention_id)
    if niveau_id:
        cond.append(Etudiant.niveau_info.has(EtudiantNiveau.niveauetude_id == niveau_id))
    if disponible is not None:
        cond.append(Etudiant.dispo.has(Disponibilite.disponible.is_(disponible)))
    total = db.scalar(select(func.count()).select_from(Etudiant).where(*cond)) or 0
    stmt = (select(Etudiant).where(*cond).order_by(Etudiant.nom).offset((page - 1) * taille).limit(taille)
            .options(selectinload(Etudiant.cvs).selectinload(CV.competences)))
    items = [etudiant_resume(e) for e in db.scalars(stmt).unique()]
    return EtudiantPage(total=total, items=items)
