"""Hybrid retrieval logic — pure functions and the relevance gate, no model."""
from onssa_rag.retriever import RetrievalResult, Retriever, tokenize


def test_tokenize_strips_accents_stopwords_and_stems():
    tokens = tokenize("Quelles sont les missions de l'ONSSA à l'exportation ?")
    assert "onssa" in tokens
    assert "missio" in tokens  # 6-char prefix stem
    assert "export" in tokens
    assert "les" not in tokens
    assert "de" not in tokens


def test_stemming_folds_french_morphology():
    assert tokenize("organisation") == tokenize("organisé")
    assert tokenize("importation") == tokenize("importer")


def test_tokenize_keeps_acronyms():
    assert tokenize("C'est quoi le SIPS ?") == ["sips"]


def test_rrf_prefers_docs_ranked_high_in_both_lists():
    fused = Retriever._rrf([[1, 2, 3], [2, 1, 4]])
    assert set(fused[:2]) == {1, 2}  # present in both lists -> top
    assert set(fused) == {1, 2, 3, 4}


def test_rrf_weights_favor_the_heavier_ranking():
    fused = Retriever._rrf([[1, 2], [3, 4]], weights=[1.0, 0.5])
    assert fused[:2] == [1, 2]  # full-weight list dominates the downweighted one


def test_relevance_gate(monkeypatch):
    from onssa_rag import config

    monkeypatch.setattr(config, "SIMILARITY_THRESHOLD", 0.5)
    monkeypatch.setattr(config, "BM25_GATE", 8.0)
    assert not RetrievalResult([], best_vector_score=0.2, best_bm25_score=1.0).relevant
    assert RetrievalResult([], best_vector_score=0.9, best_bm25_score=0.0).relevant
    assert RetrievalResult([], best_vector_score=0.2, best_bm25_score=20.0).relevant
