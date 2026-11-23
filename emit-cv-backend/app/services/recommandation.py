"""Calcul du classement d'une offre, par blocs (mémoire bornée), avec traçabilité (ScoringRun).

Principe pour tenir à plusieurs milliers de CV :
  1. les caractéristiques de chaque CV sont déjà calculées et mises en cache (table cv_analyse) : aucun document n'est relu ;
  2. les CV sont lus par blocs de `SCORING_CHUNK` ; passe 1 : ajustement du TF-IDF sur le corpus (en flux) ; passe 2 : notation ;
  3. les résultats sont écrits par blocs ; le rang final est attribué en une seule mise à jour groupée.
"""
import logging
import time
from datetime import date

from sqlalchemy import func, select, update
from sqlalchemy.orm import Session, selectinload

from app.ai.embeddings import get_engine
from app.ai.ranking import noter_lot
from app.ai.scoring import POIDS, VERSION_ALGORITHME, CandidateData, OfferData, ScoreResult
from app.core.config import settings
from app.models import (CV, STATUT_RECOMMANDEE, Candidature, CVAnalyse, CVInfos, Disponibilite, Etudiant, EtudiantNiveau, Mention,
                        NiveauEtude, Offre, Recommandation, RecommandationDetail, ScoringRun, utcnow)
from app.services import analyse as analyse_service
from app.services.journal import notifier

log = logging.getLogger("emit.reco")


def cv_publie_recent(etudiant: Etudiant) -> CV | None:
    publies = [c for c in etudiant.cvs if c.statut == "publie"]
    return max(publies, key=lambda c: c.date_maj, default=None)


def build_offer(offre: Offre) -> OfferData:
    return OfferData(
        id=offre.id, type=offre.type, titre=offre.titre, missions=offre.description or "",
        criteres=[{"competence": c.competence, "poids": c.poids, "niveau_requis": c.niveau_requis, "obligatoire": c.obligatoire} for c in offre.criteres],
        specialites_ids={m.id for m in offre.mentions}, specialites_noms=[m.nom for m in offre.mentions],
        niveau_min_rang=offre.niveau_min.rang if offre.niveau_min else None, niveau_min_nom=offre.niveau_min.nom if offre.niveau_min else None,
        niveau_obligatoire=offre.niveau_obligatoire, periode_debut=offre.periode_debut, periode_fin=offre.periode_fin,
    )


def ids_cv_eligibles(db: Session) -> list[tuple[int, int]]:
    """(cv_id, etudiant_id) du CV publié le plus récent de chaque étudiant — requête SQL, sans charger de CV."""
    rn = func.row_number().over(partition_by=CV.etudiant_id, order_by=(CVInfos.date_maj.desc(), CV.id.desc())).label("rn")
    sub = select(CV.id.label("cv_id"), CV.etudiant_id.label("etu"), rn).join(CVInfos, CVInfos.cv_id == CV.id, isouter=True).where(CV.statut == "publie").subquery()
    return [(r.cv_id, r.etu) for r in db.execute(select(sub.c.cv_id, sub.c.etu).where(sub.c.rn == 1).order_by(sub.c.cv_id))]


def _assurer_analyses(db: Session, cv_ids: list[int]) -> None:
    """Analyse sur-le-champ les CV publiés dont l'analyse n'est pas encore faite (cas de repli ; le worker les traite normalement avant)."""
    for i in range(0, len(cv_ids), 1000):
        morceau = cv_ids[i:i + 1000]
        prets = {r for (r,) in db.execute(select(CVAnalyse.cv_id).where(CVAnalyse.cv_id.in_(morceau), CVAnalyse.statut.in_(("ok", "ocr_requis", "vide", "echec"))))}
        for cid in morceau:
            if cid not in prets:
                analyse_service.analyser_cv(db, cid)


def _charger_bloc(db: Session, cv_ids: list[int]) -> list[CandidateData]:
    stmt = (select(CV.id, CV.etudiant_id, CVAnalyse.caracteristiques, Etudiant.mention_id, Mention.nom, NiveauEtude.nom, Disponibilite.disponible,
                   Disponibilite.datedebut, Disponibilite.datefin, Disponibilite.type)
            .join(Etudiant, Etudiant.id == CV.etudiant_id).join(Mention, Mention.id == Etudiant.mention_id)
            .outerjoin(CVAnalyse, CVAnalyse.cv_id == CV.id)
            .outerjoin(EtudiantNiveau, EtudiantNiveau.etudiant_id == Etudiant.id).outerjoin(NiveauEtude, NiveauEtude.id == EtudiantNiveau.niveauetude_id)
            .outerjoin(Disponibilite, Disponibilite.etudiant_id == Etudiant.id).where(CV.id.in_(cv_ids)).order_by(CV.id))
    out = []
    for cid, eid, carac, m_id, m_nom, n_nom, dispo, d0, d1, dtype in db.execute(stmt):
        carac = carac or {}
        niv = NiveauEtude(nom=n_nom) if n_nom else None
        out.append(CandidateData(
            etudiant_id=eid, cv_id=cid, competences=carac.get("competences", []), items=carac.get("items", []),
            formations_texte=carac.get("formations_texte", ""), mention_id=m_id, mention_nom=m_nom,
            niveau_rang=niv.rang if niv else None, niveau_nom=n_nom, disponible=True if dispo is None else dispo,
            dispo_debut=d0, dispo_fin=d1, dispo_type=dtype or "tous"))
    return out


def _blocs(db: Session, cv_ids: list[int]):
    for i in range(0, len(cv_ids), settings.scoring_chunk):
        yield _charger_bloc(db, cv_ids[i:i + settings.scoring_chunk])


def recompute_offer(db: Session, offre_id: int, declencheur: str = "", notify_new: bool = False) -> dict:
    """Recalcule scores et classement de tous les CV publiés pour une offre. Retourne {run_id, nb, duree_ms}."""
    t0 = time.perf_counter()
    offre = db.scalar(select(Offre).where(Offre.id == offre_id).options(selectinload(Offre.criteres), selectinload(Offre.mentions), selectinload(Offre.infos)))
    if offre is None:
        return {"run_id": None, "nb": 0, "duree_ms": 0}
    offer = build_offer(offre)
    engine = get_engine()
    run = ScoringRun(offre_id=offre.id, version_algorithme=VERSION_ALGORITHME, poids=dict(POIDS), moteur_ia=engine.name, declencheur=declencheur,
                     criteres_offre={"titre": offer.titre, "type": offer.type, "criteres": offer.criteres, "specialites": offer.specialites_noms,
                                     "niveau_min": offer.niveau_min_nom, "niveau_obligatoire": offer.niveau_obligatoire,
                                     "periode_debut": str(offer.periode_debut) if offer.periode_debut else None,
                                     "periode_fin": str(offer.periode_fin) if offer.periode_fin else None})
    db.add(run)
    db.commit()
    try:
        eligibles = ids_cv_eligibles(db)
        cv_ids = [c for c, _ in eligibles]
        _assurer_analyses(db, cv_ids)
        # Passe 1 : ajustement du corpus (en flux, bloc par bloc)
        engine.fit_corpus(t for bloc in _blocs(db, cv_ids) for c in bloc for it in c.items for t in (it["texte"], it["titre"]))
        # Passe 2 : notation et écriture par blocs
        existantes = {}
        for i in range(0, len(eligibles), 1000):
            etus = [e for _, e in eligibles[i:i + 1000]]
            for cand, etu_id in db.execute(select(Candidature, CV.etudiant_id).join(CV, CV.id == Candidature.cv_id)
                                           .where(Candidature.offre_id == offre.id, CV.etudiant_id.in_(etus))
                                           .options(selectinload(Candidature.recommandation).selectinload(Recommandation.info))):
                existantes[etu_id] = cand
        vus, tri = set(), []
        for bloc in _blocs(db, cv_ids):
            for r in noter_lot(offer, bloc, engine):
                r.detail["run_id"] = run.id
                cand = existantes.get(r.etudiant_id)
                premiere = cand is None or cand.recommandation is None
                if cand is None:
                    cand = Candidature(offre_id=offre.id, cv_id=r.cv_id, statut=STATUT_RECOMMANDEE)
                    db.add(cand)
                    existantes[r.etudiant_id] = cand
                elif cand.statut == STATUT_RECOMMANDEE:
                    cand.cv_id = r.cv_id
                reco = cand.recommandation
                if reco is None:
                    reco = Recommandation()
                    cand.recommandation = reco
                reco.score, reco.statut, reco.date = round(r.score), "proposee", utcnow()
                reco.detail = r.detail
                reco.info.elimine, reco.info.run_id = r.elimine, run.id
                if notify_new and premiere and r.score >= settings.ai_notify_threshold and not r.elimine:
                    notifier(db, r.etudiant_id, f"Nouvelle offre qui vous correspond ({r.score:.0f}/100) : {offre.titre}")
                vus.add(r.etudiant_id)
                tri.append((reco, r))
            db.flush()
            db.commit()
        # Rang final (une seule mise à jour groupée) : conformes d'abord, puis éliminés ; score décroissant
        tri.sort(key=lambda x: (x[1].elimine, -x[1].score, -len(x[1].detail["criteres"]["competences"]["elements"]["trouvees"]), x[1].etudiant_id))
        db.execute(update(RecommandationDetail), [{"recommandation_id": reco.id, "rang": i + 1} for i, (reco, _) in enumerate(tri)])
        # Étudiants devenus non éligibles (CV dépublié ou supprimé…) : on retire leurs simples recommandations (jamais une vraie candidature)
        perimees = [c for c, etu_id in db.execute(select(Candidature, CV.etudiant_id).join(CV, CV.id == Candidature.cv_id)
                                                  .where(Candidature.offre_id == offre.id, Candidature.statut == STATUT_RECOMMANDEE)) if etu_id not in vus]
        for cand in perimees:
            db.delete(cand)
        run.statut, run.nb_candidats, run.duree_ms = "termine", len(tri), int((time.perf_counter() - t0) * 1000)
        db.commit()
        log.info("Classement offre %s : %s candidats en %s ms (moteur %s)", offre.id, len(tri), run.duree_ms, engine.name)
        return {"run_id": run.id, "nb": len(tri), "duree_ms": run.duree_ms}
    except Exception as exc:
        db.rollback()
        run = db.get(ScoringRun, run.id)
        run.statut, run.erreur = "echoue", str(exc)[:1500]
        db.commit()
        raise


def offres_ouvertes(db: Session) -> list[Offre]:
    return [o for o in db.scalars(select(Offre).where(Offre.statut == "publiee").options(selectinload(Offre.infos))) if o.est_ouverte]
