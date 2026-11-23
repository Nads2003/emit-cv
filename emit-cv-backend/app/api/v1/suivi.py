"""Côté étudiant : recommandations d'offres et suivi des candidatures. Côté admin : statistiques, historique, suivi des traitements."""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.core.deps import require_admin, require_etudiant
from app.db.session import get_db
from app.models import (CV, STATUT_RECOMMANDEE, Administrateur, Candidature, CVAnalyse, Disponibilite, Etudiant, EtudiantAutorise, Historique, Offre,
                        Recommandation, Tache, Utilisateur)
from app.api.v1.offres import _OPTS, _vue_etudiant
from app.schemas.offre import CandidatureOut, OffreEtudiantOut
from app.services import taches

router = APIRouter(tags=["Suivi"])


@router.get("/recommandations/moi", response_model=list[OffreEtudiantOut], summary="Offres recommandées pour moi, classées par score")
def mes_recommandations(etu: Etudiant = Depends(require_etudiant), db: Session = Depends(get_db)):
    cands = db.scalars(select(Candidature).join(CV, CV.id == Candidature.cv_id).join(Recommandation, Recommandation.candidature_id == Candidature.id)
                       .where(CV.etudiant_id == etu.id).order_by(Recommandation.score.desc())
                       .options(selectinload(Candidature.recommandation).selectinload(Recommandation.info))).all()
    out = []
    for c in cands:
        o = db.scalar(select(Offre).where(Offre.id == c.offre_id).options(*_OPTS))
        if o and o.est_ouverte:
            out.append(_vue_etudiant(o, c, True))
    return out


@router.get("/candidatures/moi", response_model=list[CandidatureOut], summary="Mes candidatures")
def mes_candidatures(etu: Etudiant = Depends(require_etudiant), db: Session = Depends(get_db)):
    rows = db.scalars(select(Candidature).join(CV, CV.id == Candidature.cv_id).where(CV.etudiant_id == etu.id, Candidature.statut != STATUT_RECOMMANDEE)
                      .order_by(Candidature.date.desc()).options(selectinload(Candidature.offre))).all()
    return [CandidatureOut(id=c.id, offre_id=c.offre_id, offre_titre=c.offre.titre, offre_statut=c.offre.statut, statut=c.statut, date=c.date, a_postule=c.a_postule) for c in rows]


@router.get("/admin/stats", summary="Chiffres clés du tableau de bord administrateur")
def stats(_: Administrateur = Depends(require_admin), db: Session = Depends(get_db)):
    def n(stmt):
        return db.scalar(stmt) or 0
    return {
        "etudiants": n(select(func.count()).select_from(Etudiant)),
        "etudiants_autorises": n(select(func.count()).select_from(EtudiantAutorise)),
        "cv_publies": n(select(func.count()).select_from(CV).where(CV.statut == "publie")),
        "offres_publiees": n(select(func.count()).select_from(Offre).where(Offre.statut == "publiee")),
        "offres_cloturees": n(select(func.count()).select_from(Offre).where(Offre.statut == "cloturee")),
        "candidatures": n(select(func.count()).select_from(Candidature).where(Candidature.statut != STATUT_RECOMMANDEE)),
        "selectionnes": n(select(func.count()).select_from(Candidature).where(Candidature.statut == "selectionne")),
        "etudiants_disponibles": n(select(func.count()).select_from(Disponibilite).where(Disponibilite.disponible.is_(True))),
        "analyses_en_echec": n(select(func.count()).select_from(CVAnalyse).where(CVAnalyse.statut.in_(("echec", "ocr_requis")))),
        "taches_echouees": n(select(func.count()).select_from(Tache).where(Tache.statut == "echoue")),
    }


@router.get("/admin/historique", summary="Journal d'activité (admin)")
def historique(limite: int = Query(50, ge=1, le=200), _: Administrateur = Depends(require_admin), db: Session = Depends(get_db)):
    rows = db.execute(select(Historique, Utilisateur.nom).outerjoin(Utilisateur, Utilisateur.id == Historique.utilisateur_id)
                      .order_by(Historique.date.desc()).limit(limite)).all()
    return [{"id": h.id, "action": h.action, "date": h.date, "utilisateur": nom} for h, nom in rows]


# ------------------------------------------------------------------ Suivi des traitements asynchrones
@router.get("/admin/taches", summary="État de la file de tâches (analyses de CV, calculs de classement)")
def etat_taches(statut: str | None = Query(None, pattern="^(en_attente|en_cours|termine|echoue)$"), limite: int = Query(30, ge=1, le=200),
                _: Administrateur = Depends(require_admin), db: Session = Depends(get_db)):
    stmt = select(Tache).order_by(Tache.id.desc()).limit(limite)
    if statut:
        stmt = stmt.where(Tache.statut == statut)
    recentes = [{"id": t.id, "type": t.type, "cible_id": t.cible_id, "statut": t.statut, "tentatives": t.tentatives, "erreur": t.erreur,
                 "declencheur": t.declencheur, "cree_le": t.cree_le, "termine_le": t.termine_le} for t in db.scalars(stmt)]
    return {"resume": taches.resume(db), "recentes": recentes}


@router.post("/admin/taches/{tache_id}/relancer", summary="Relancer UNE tâche échouée")
def relancer(tache_id: int, _: Administrateur = Depends(require_admin), db: Session = Depends(get_db)):
    if not taches.relancer(db, tache_id):
        raise HTTPException(409, "Seule une tâche échouée peut être relancée.")
    return {"statut": "en_attente"}


@router.post("/admin/taches/relancer-echouees", summary="Relancer toutes les tâches échouées (les autres ne sont pas retraitées)")
def relancer_toutes(_: Administrateur = Depends(require_admin), db: Session = Depends(get_db)):
    return {"relancees": taches.relancer_echouees(db)}
