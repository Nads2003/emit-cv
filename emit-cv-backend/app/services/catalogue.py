"""Catalogue de compétences : un CritereOffre référence une ligne `competence` (cv_id NULL = entrée de catalogue)."""
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.ai.skills_taxonomy import canonical
from app.models import Competence


def competence_catalogue(db: Session, nom: str) -> Competence:
    """Retourne (en la créant au besoin) la compétence de catalogue correspondant au nom canonique."""
    nom = canonical(nom)
    comp = db.scalar(select(Competence).where(Competence.cv_id.is_(None), func.lower(Competence.nom) == nom.lower()))
    if comp is None:
        comp = Competence(nom=nom, cv_id=None, niveau_maitrise=None)
        db.add(comp)
        db.flush()
    return comp
