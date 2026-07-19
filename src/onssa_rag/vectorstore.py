"""FAISS index persistence: build, save, load, search + manifest.

The manifest records the embedding model and corpus stats so the app can
refuse to serve an index built with a different embedding model, and so the
sidebar can display document counts without loading everything.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import faiss
import numpy as np
import pandas as pd

from . import config

INDEX_FILE = "faiss.index"
CHUNKS_FILE = "chunks.parquet"
SECTIONS_FILE = "sections.parquet"
MANIFEST_FILE = "manifest.json"


def build_index(embeddings: np.ndarray) -> faiss.Index:
    index = faiss.IndexFlatIP(embeddings.shape[1])
    index.add(embeddings)
    return index


def save(
    index: faiss.Index,
    chunks: pd.DataFrame,
    sections: pd.DataFrame,
    manifest: dict,
    index_dir: Path = config.INDEX_DIR,
) -> None:
    index_dir.mkdir(parents=True, exist_ok=True)
    faiss.write_index(index, str(index_dir / INDEX_FILE))
    chunks.to_parquet(index_dir / CHUNKS_FILE, index=False)
    sections.to_parquet(index_dir / SECTIONS_FILE, index=False)
    manifest = {
        **manifest,
        "built_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }
    (index_dir / MANIFEST_FILE).write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8"
    )


def load(index_dir: Path = config.INDEX_DIR):
    index = faiss.read_index(str(index_dir / INDEX_FILE))
    chunks = pd.read_parquet(index_dir / CHUNKS_FILE)
    sections = pd.read_parquet(index_dir / SECTIONS_FILE)
    manifest = json.loads((index_dir / MANIFEST_FILE).read_text(encoding="utf-8"))
    return index, chunks, sections, manifest


def search(index: faiss.Index, query_vec: np.ndarray, k: int):
    scores, idx = index.search(query_vec, k)
    return scores[0], idx[0]
