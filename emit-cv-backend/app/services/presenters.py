"""Fonctions de présentation partagées entre routeurs (modèle -> schéma de sortie)."""
from app.models import Etudiant
from app.schemas.etudiant import EtudiantMoiOut, EtudiantResume
from app.services.recommandation import cv_publie_recent


def etudiant_moi(e: Etudiant) -> EtudiantMoiOut:
    p = e.profil
    return EtudiantMoiOut(
        id=e.id, nom=e.nom, email=e.email, matricule=e.matricule,
        mention_id=e.mention_id, mention_nom=e.mention.nom if e.mention else None,
        niveau_id=e.niveau_id, niveau_nom=e.niveau.nom if e.niveau else None,
        telephone=p.telephone if p else None, adresse=p.adresse if p else None, a_photo=bool(p and p.photo),
        disponible=e.disponible, dispo_debut=e.dispo_debut, dispo_fin=e.dispo_fin, dispo_type=e.dispo_type,
    )


def etudiant_resume(e: Etudiant) -> EtudiantResume:
    cv = cv_publie_recent(e)
    return EtudiantResume(
        id=e.id, nom=e.nom, matricule=e.matricule, email=e.email,
        mention_nom=e.mention.nom if e.mention else None, niveau_nom=e.niveau.nom if e.niveau else None,
        disponible=e.disponible, dispo_type=e.dispo_type,
        cv_id=cv.id if cv else None, cv_titre=cv.titre if cv else None,
        competences=[c.nom for c in (cv.competences if cv else [])][:8],
        a_photo=bool(e.profil and e.profil.photo),
    )
