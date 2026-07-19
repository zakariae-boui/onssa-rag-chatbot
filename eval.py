"""Retrieval evaluation: hit@5 over data/eval_questions.yaml.

For each question, checks whether the expected ONSSA page URL appears among the
top-k retrieved sources. Reports naive (vector-only) vs hybrid (vector + BM25)
numbers so retrieval choices are justified with measurements.

Usage:
    python eval.py

Implemented in Phase 3 (see PROJECT_PLAN.md, section 11).
"""


def main() -> None:
    raise SystemExit("Not implemented yet — Phase 3 (see PROJECT_PLAN.md, section 11).")


if __name__ == "__main__":
    main()
