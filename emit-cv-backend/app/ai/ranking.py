"""Calcul des similarités (par éléments) puis scoring et classement d'un lot de candidats."""
from app.ai.embeddings import SimilarityEngine, get_engine
from app.ai.scoring import CandidateData, ItemSims, OfferData, ScoreResult, classer, effective_criteria, score_candidate
from app.ai.skills_taxonomy import mask_skills


def noter_lot(offer: OfferData, candidates: list[CandidateData], engine: SimilarityEngine | None = None) -> list[ScoreResult]:
    """Note un lot de candidats (non trié). Les similarités des éléments sont calculées d'un seul appel au moteur pour tout le lot."""
    if not candidates:
        return []
    engine = engine or get_engine()
    criteres, deduits = effective_criteria(offer)
    missions = mask_skills(offer.missions)           # compétences retirées : déjà notées au critère 1
    titre_offre = f"{offer.titre} {offer.type}"
    textes = [it["texte"] for c in candidates for it in c.items]
    titres = [it["titre"] for c in candidates for it in c.items]
    s_miss = engine.similarities(missions, textes) if textes else []
    s_tit = engine.similarities(titre_offre, titres) if titres else []
    resultats, i = [], 0
    for c in candidates:
        n = len(c.items)
        sims = ItemSims(missions=s_miss[i:i + n], titres=s_tit[i:i + n])
        i += n
        r = score_candidate(offer, c, sims, criteres, deduits)
        r.detail["moteur_ia"] = engine.name
        resultats.append(r)
    return resultats


def rank_candidates(offer: OfferData, candidates: list[CandidateData], engine: SimilarityEngine | None = None) -> list[tuple[int, ScoreResult]]:
    """Version « en mémoire » (petits volumes, tests) : note + classe."""
    return classer(noter_lot(offer, candidates, engine))
