"""Données de référence créées au démarrage (idempotent). Modifiables ensuite en base."""
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Mention, ModelCV, NiveauEtude

MENTIONS = ["Informatique", "Gestion", "Management", "Communication"]
NIVEAUX = ["L1", "L2", "L3", "M1", "M2"]
MODELES = [
    ("Classique", "Sobre, une colonne, idéal pour tous les domaines.", "classique"),
    ("Moderne", "Bandeau coloré et compétences en évidence.", "moderne"),
    ("Académique", "Met en avant formations et projets.", "academique"),
]


def seed_referentiels(db: Session) -> None:
    for nom in MENTIONS:
        mention = db.scalar(select(Mention).where(Mention.nom == nom))
        if mention is None:
            mention = Mention(nom=nom)
            db.add(mention)
            db.flush()
        existants = {n.nom for n in db.scalars(select(NiveauEtude).where(NiveauEtude.mention_id == mention.id))}
        for n in NIVEAUX:
            if n not in existants:
                db.add(NiveauEtude(nom=n, mention_id=mention.id))
    if not db.scalar(select(ModelCV.id).limit(1)):
        db.add_all(ModelCV(nom=n, description=d, apercu=a) for n, d, a in MODELES)
    db.commit()
