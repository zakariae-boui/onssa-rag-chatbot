"""Sentence-transformers wrapper with E5-style query/passage prefixes.

E5-family models are trained with asymmetric "query: " / "passage: " prefixes;
omitting them measurably degrades retrieval. Other models are used as-is.
"""
from __future__ import annotations

import numpy as np
from sentence_transformers import SentenceTransformer

from . import config


class Embedder:
    def __init__(self, model_name: str = config.EMBEDDING_MODEL):
        self.model_name = model_name
        self.model = SentenceTransformer(model_name)
        self._e5 = "e5" in model_name.lower()

    @property
    def dim(self) -> int:
        return self.model.get_embedding_dimension()

    def encode_passages(
        self, texts: list[str], batch_size: int = 32, progress: bool = False
    ) -> np.ndarray:
        if self._e5:
            texts = [f"passage: {t}" for t in texts]
        return self.model.encode(
            texts,
            batch_size=batch_size,
            normalize_embeddings=True,
            show_progress_bar=progress,
        ).astype("float32")

    def encode_query(self, text: str) -> np.ndarray:
        if self._e5:
            text = f"query: {text}"
        return self.model.encode([text], normalize_embeddings=True).astype("float32")
