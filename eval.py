"""Retrieval evaluation: hit@5 over data/eval_questions.yaml.

For each question, checks whether the expected ONSSA page URL appears among
the top-5 unique page URLs returned by retrieval. Compares naive (vector-only)
against hybrid (vector + BM25 + RRF) so the retrieval choice is justified with
numbers, not fashion.

Usage:
    python eval.py
"""
from __future__ import annotations

import sys

import yaml

from onssa_rag import config
from onssa_rag.retriever import Retriever

K = 5


def _norm(url: str) -> str:
    return url.rstrip("/")


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    with open(config.EVAL_QUESTIONS, encoding="utf-8") as fh:
        entries = yaml.safe_load(fh)

    retriever = Retriever()
    totals = {"vector": 0, "hybrid": 0}
    rows = []
    for entry in entries:
        question = entry["question"]
        accepted = {_norm(u) for u in entry.get("expected_urls") or [entry["expected_url"]]}
        hits = {}
        for mode, use_bm25 in (("vector", False), ("hybrid", True)):
            urls = {_norm(u) for u in retriever.top_urls(question, k=K, use_bm25=use_bm25)}
            hits[mode] = bool(accepted & urls)
            totals[mode] += hits[mode]
        rows.append((question, hits["vector"], hits["hybrid"]))

    width = max(len(q) for q, *_ in rows)
    print(f"{'question':<{width}}  vector  hybrid")
    for question, vec_hit, hyb_hit in rows:
        vec = "hit " if vec_hit else "MISS"
        hyb = "hit" if hyb_hit else "MISS"
        print(f"{question:<{width}}  {vec}    {hyb}")
    n = len(rows)
    print(f"\nhit@{K}: vector-only {totals['vector']}/{n} — hybrid {totals['hybrid']}/{n}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
