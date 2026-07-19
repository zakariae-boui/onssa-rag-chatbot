"""FAISS store roundtrip with synthetic vectors (no model download needed)."""
import numpy as np
import pandas as pd

from onssa_rag import vectorstore


def test_roundtrip_and_search(tmp_path):
    rng = np.random.default_rng(0)
    vecs = rng.normal(size=(10, 8)).astype("float32")
    vecs /= np.linalg.norm(vecs, axis=1, keepdims=True)

    index = vectorstore.build_index(vecs)
    chunks = pd.DataFrame({"chunk_id": [f"c{i}" for i in range(10)], "text": ["x"] * 10})
    sections = pd.DataFrame({"parent_id": ["s0"], "text": ["y"]})
    vectorstore.save(index, chunks, sections, {"dim": 8}, index_dir=tmp_path)

    index2, chunks2, sections2, manifest = vectorstore.load(tmp_path)
    assert len(chunks2) == 10
    assert len(sections2) == 1
    assert manifest["dim"] == 8
    assert "built_at" in manifest

    scores, idx = vectorstore.search(index2, vecs[3:4], k=1)
    assert idx[0] == 3
    assert scores[0] > 0.99
