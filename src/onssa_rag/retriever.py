"""Hybrid retrieval: FAISS vector search + BM25 keyword search, RRF fusion,
relevance gate, and parent-section expansion (small-to-big).

Vector search captures paraphrases ("comment joindre l'office" -> contacts);
BM25 captures exact tokens (SIPS, Codex, numéros de loi) that embeddings
dilute. Reciprocal Rank Fusion merges both rankings without score calibration.
"""
from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass

import numpy as np
from rank_bm25 import BM25Okapi

from . import config, vectorstore
from .embeddings import Embedder

RRF_K = 60  # standard rank-discount constant

_STOPWORDS = {
    "au", "aux", "avec", "ce", "ces", "cette", "comment", "dans", "de", "des", "du",
    "elle", "en", "est", "et", "il", "ils", "je", "la", "le", "les", "leur", "lui",
    "mais", "ne", "nous", "on", "ou", "par", "pas", "pour", "quand", "que", "quel",
    "quelle", "quelles", "quels", "qui", "quoi", "sa", "se", "ses", "son", "sont",
    "sur", "tout", "toute", "toutes", "tous", "un", "une", "vous",
}


def tokenize(text: str) -> list[str]:
    """Lowercase, strip accents, drop stopwords, 6-char prefix stem.

    The prefix stem folds French morphological variants together
    (organisation/organisé -> organi, importation/importer -> import),
    which BM25 needs since it only matches exact tokens.
    """
    text = unicodedata.normalize("NFD", text.lower())
    text = "".join(c for c in text if not unicodedata.combining(c))
    tokens = [t for t in re.split(r"[^a-z0-9]+", text) if len(t) >= 2 and t not in _STOPWORDS]
    return [t[:6] for t in tokens]


@dataclass
class Passage:
    url: str
    title: str
    heading: str
    text: str


@dataclass
class RetrievalResult:
    passages: list[Passage]
    best_vector_score: float
    best_bm25_score: float

    @property
    def relevant(self) -> bool:
        """Gate: either leg must show a confident hit, otherwise the caller
        answers « information non trouvée » instead of generating."""
        return (
            self.best_vector_score >= config.SIMILARITY_THRESHOLD
            or self.best_bm25_score >= config.BM25_GATE
        )


class Retriever:
    def __init__(self, embedder: Embedder | None = None):
        self.index, self.chunks, sections, self.manifest = vectorstore.load()
        if self.manifest["embedding_model"] != config.EMBEDDING_MODEL:
            raise RuntimeError(
                f"L'index a été construit avec {self.manifest['embedding_model']} "
                f"mais EMBEDDING_MODEL={config.EMBEDDING_MODEL} — relancez ingest.py."
            )
        self.embedder = embedder or Embedder()
        self._bm25 = BM25Okapi([tokenize(t) for t in self.chunks["text"]])
        self._sections = sections.set_index("parent_id")

    def _vector_ranking(self, query: str, n: int) -> tuple[list[int], float]:
        scores, idx = vectorstore.search(self.index, self.embedder.encode_query(query), n)
        order = [int(i) for i in idx if i >= 0]
        return order, float(scores[0]) if len(scores) else 0.0

    def _bm25_ranking(self, query: str, n: int) -> tuple[list[int], float]:
        scores = self._bm25.get_scores(tokenize(query))
        order = np.argsort(scores)[::-1][:n]
        return [int(i) for i in order], float(scores[order[0]]) if len(order) else 0.0

    @staticmethod
    def _rrf(rankings: list[list[int]], weights: list[float] | None = None) -> list[int]:
        weights = weights or [1.0] * len(rankings)
        fused: dict[int, float] = {}
        for ranking, weight in zip(rankings, weights):
            for rank, doc in enumerate(ranking):
                fused[doc] = fused.get(doc, 0.0) + weight / (RRF_K + rank + 1)
        return sorted(fused, key=lambda d: fused[d], reverse=True)

    def rank(self, query: str, use_bm25: bool = True) -> tuple[list[int], float, float]:
        """Fused chunk ranking + best raw score of each leg (for the gate)."""
        n = config.RETRIEVER_CANDIDATES
        vec_order, best_vec = self._vector_ranking(query, n)
        if not use_bm25:
            return vec_order, best_vec, 0.0
        bm_order, best_bm = self._bm25_ranking(query, config.BM25_CANDIDATES)
        fused = self._rrf([vec_order, bm_order], [1.0, config.BM25_WEIGHT])
        return fused, best_vec, best_bm

    def top_urls(self, query: str, k: int = 5, use_bm25: bool = True) -> list[str]:
        """Ranked unique page URLs — used by eval.py for hit@k."""
        order, _, _ = self.rank(query, use_bm25=use_bm25)
        urls: list[str] = []
        for i in order:
            url = self.chunks.iloc[i]["url"]
            if url not in urls:
                urls.append(url)
            if len(urls) == k:
                break
        return urls

    def retrieve(
        self, query: str, k: int | None = None, max_chars: int | None = None
    ) -> RetrievalResult:
        """Top-k fused chunks expanded to their full parent sections."""
        k = k or config.TOP_K
        max_chars = max_chars or config.MAX_CONTEXT_CHARS
        order, best_vec, best_bm = self.rank(query)
        passages: list[Passage] = []
        seen: set[str] = set()
        total = 0
        for i in order:
            chunk = self.chunks.iloc[i]
            parent_id = chunk["parent_id"]
            if parent_id in seen:
                continue
            seen.add(parent_id)
            section = self._sections.loc[parent_id]
            text = str(section["text"])
            passages.append(
                Passage(
                    url=chunk["url"],
                    title=chunk["title"],
                    heading=str(section["heading"]),
                    text=text,
                )
            )
            total += len(text)
            if len(passages) >= k or total >= max_chars:
                break
        return RetrievalResult(passages, best_vec, best_bm)
