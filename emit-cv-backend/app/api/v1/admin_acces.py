"""Administration de la liste des étudiants autorisés : import Excel (aperçu puis confirmation) et consultation."""
from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from pydantic import BaseModel
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.core.deps import require_admin
from app.db.session import get_db
from app.models import Administrateur, EtudiantAutorise, ImportLigne, ImportListe
from app.services import acces

router = APIRouter(prefix="/admin/etudiants-autorises", tags=["Étudiants autorisés"])


class ConfirmationIn(BaseModel):
    ignorer_erreurs: bool = False


def _resume(imp: ImportListe) -> dict:
    return {"id": imp.id, "nom_fichier": imp.nom_fichier, "statut": imp.statut, "nb_lignes": imp.nb_lignes, "nb_nouveaux": imp.nb_nouveaux,
            "nb_maj": imp.nb_maj, "nb_inchanges": imp.nb_inchanges, "nb_erreurs": imp.nb_erreurs, "cree_le": imp.cree_le, "confirme_le": imp.confirme_le}


@router.post("/import", status_code=201, summary="1) Téléverser un fichier Excel : APERÇU (rien n'est appliqué)")
async def apercu(file: UploadFile = File(...), admin: Administrateur = Depends(require_admin), db: Session = Depends(get_db)):
    data = await file.read(acces.MAX_XLSX + 1)
    imp = acces.apercu_import(db, admin, file.filename or "liste.xlsx", data)
    lignes = db.scalars(select(ImportLigne).where(ImportLigne.import_id == imp.id).order_by(ImportLigne.numero)).all()
    return {**_resume(imp), "lignes": [{"numero": l.numero, "nom": l.nom, "prenom": l.prenom, "email": l.email, "matricule": l.matricule, "action": l.action, "message": l.message}
                                       for l in lignes if l.action == "erreur"][:200],
            "extrait": [{"numero": l.numero, "nom": l.nom, "prenom": l.prenom, "email": l.email, "matricule": l.matricule, "action": l.action} for l in lignes[:20]]}


@router.post("/import/{import_id}/confirmer", summary="2) Confirmer l'import (applique les changements)")
def confirmer(import_id: int, body: ConfirmationIn | None = None, admin: Administrateur = Depends(require_admin), db: Session = Depends(get_db)):
    return _resume(acces.confirmer_import(db, admin, import_id, bool(body and body.ignorer_erreurs)))


@router.post("/import/{import_id}/annuler", status_code=204, summary="Annuler un aperçu")
def annuler(import_id: int, admin: Administrateur = Depends(require_admin), db: Session = Depends(get_db)):
    imp = db.get(ImportListe, import_id)
    if imp is None or imp.statut != "apercu":
        raise HTTPException(404, "Aperçu introuvable.")
    imp.statut = "annule"
    db.commit()


@router.get("/imports", summary="Historique des imports")
def imports(_: Administrateur = Depends(require_admin), db: Session = Depends(get_db)):
    return [_resume(i) for i in db.scalars(select(ImportListe).order_by(ImportListe.id.desc()).limit(30))]


@router.get("", summary="Liste des étudiants autorisés")
def lister(q: str | None = Query(None, max_length=100), inscrit: bool | None = None, page: int = Query(1, ge=1), taille: int = Query(25, ge=1, le=100),
           _: Administrateur = Depends(require_admin), db: Session = Depends(get_db)):
    cond = []
    if q:
        like = f"%{q.strip()}%"
        cond.append(or_(EtudiantAutorise.nom.ilike(like), EtudiantAutorise.prenom.ilike(like), EtudiantAutorise.email.ilike(like), EtudiantAutorise.matricule.ilike(like.upper())))
    if inscrit is not None:
        cond.append(EtudiantAutorise.utilisateur_id.is_not(None) if inscrit else EtudiantAutorise.utilisateur_id.is_(None))
    total = db.scalar(select(func.count()).select_from(EtudiantAutorise).where(*cond)) or 0
    rows = db.scalars(select(EtudiantAutorise).where(*cond).order_by(EtudiantAutorise.matricule).offset((page - 1) * taille).limit(taille)).all()
    return {"total": total, "items": [{"id": a.id, "nom": a.nom, "prenom": a.prenom, "email": a.email, "matricule": a.matricule, "inscrit": a.utilisateur_id is not None} for a in rows]}
