"""Moteurs de similarité sémantique texte ↔ textes.

- TfidfEngine        : scikit-learn, local, léger. Peut être AJUSTÉ (fit) sur l'ensemble du corpus pour des poids IDF cohérents
                       d'un bloc de CV à l'autre ; le corpus est parcouru en flux (jamais chargé en entier en mémoire).
- TransformersEngine : sentence-transformers (modèle multilingue), optionnel.
`similarities(query, docs)` renvoie des valeurs normalisées dans [0, 1].
"""
import hashlib
import logging
from functools import lru_cache
from typing import Callable, Iterable, Protocol

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer

from app.core.config import settings

log = logging.getLogger("emit.ai")


class SimilarityEngine(Protocol):
    name: str

    def fit_corpus(self, texts: Iterable[str]) -> None: ...
    def similarities(self, query: str, docs: list[str]) -> list[float]: ...


class TfidfEngine:
    name = "tfidf"
    ETIREMENT = 0.30  # paramètre de calibrage : un cosinus TF-IDF offre↔texte dépasse rarement 0.30 : on étire vers [0, 1]

    def __init__(self) -> None:
        self._vec: TfidfVectorizer | None = None

    @staticmethod
    def _new() -> TfidfVectorizer:
        return TfidfVectorizer(strip_accents="unicode", lowercase=True, sublinear_tf=True, ngram_range=(1, 2), min_df=1, max_features=300_000)

    def fit_corpus(self, texts: Iterable[str]) -> None:
        """Ajuste le vocabulaire et les IDF sur tout le corpus (itérable parcouru une seule fois, en flux)."""
        vec = self._new()
        try:
            vec.fit(t for t in texts if t and t.strip())
            self._vec = vec
        except ValueError:  # corpus vide
            self._vec = None

    def similarities(self, query: str, docs: list[str]) -> list[float]:
        if not docs:
            return []
        if not query.strip():
            return [0.0] * len(docs)
        vec = self._vec
        try:
            if vec is None:  # pas de corpus global : ajustement local sur ces documents + la requête
                vec = self._new()
                matrix = vec.fit_transform(docs + [query])
                q, m = matrix[-1], matrix[:-1]
            else:
                m, q = vec.transform(docs), vec.transform([query])
        except ValueError:
            return [0.0] * len(docs)
        sims = (m @ q.T).toarray().ravel()  # lignes normalisées L2 -> cosinus
        return [float(min(1.0, max(0.0, s / self.ETIREMENT))) for s in sims]


class TransformersEngine:
    name = "transformers"

    def __init__(self, model_name: str):
        from sentence_transformers import SentenceTransformer  # dépendance optionnelle

        self.model = SentenceTransformer(model_name)
        self._cache: dict[str, np.ndarray] = {}

    def fit_corpus(self, texts: Iterable[str]) -> None:  # rien à ajuster
        return None

    def _encode(self, texts: list[str]) -> np.ndarray:
        keys = [hashlib.sha1(t.encode()).hexdigest() for t in texts]
        missing = [(k, t) for k, t in zip(keys, texts) if k not in self._cache]
        if missing:
            vecs = self.model.encode([t for _, t in missing], normalize_embeddings=True, show_progress_bar=False, batch_size=32)
            for (k, _), v in zip(missing, vecs):
                self._cache[k] = v
            if len(self._cache) > 20000:  # cache borné
                for k in list(self._cache)[:5000]:
                    self._cache.pop(k, None)
        return np.vstack([self._cache[k] for k in keys])

    def similarities(self, query: str, docs: list[str]) -> list[float]:
        if not docs:
            return []
        vecs = self._encode(docs + [query])
        cos = vecs[:-1] @ vecs[-1]
        return [float(min(1.0, max(0.0, (c - 0.15) / 0.5))) for c in cos]  # ~0.15 sans rapport, ~0.65 très proche


@lru_cache
def _engine_global() -> SimilarityEngine:
    mode = settings.ai_backend.lower()
    if mode in ("auto", "transformers"):
        try:
            e = TransformersEngine(settings.ai_model)
            log.info("Moteur IA : transformers (%s)", settings.ai_model)
            return e
        except Exception as exc:
            if mode == "transformers":
                raise
            log.warning("Transformers indisponible (%s) -> repli sur TF-IDF.", exc.__class__.__name__)
    return TfidfEngine()


def get_engine() -> SimilarityEngine:
    """Un moteur NEUF pour TF-IDF (état d'ajustement propre à chaque calcul) ; le moteur transformers est partagé (cache)."""
    e = _engine_global()
    return TfidfEngine() if isinstance(e, TfidfEngine) else e
