"""Phase 0 smoke tests: the package imports and config defaults load."""
from onssa_rag import config


def test_config_defaults_load():
    assert config.TOP_K >= 1
    assert config.CHUNK_OVERLAP < config.CHUNK_SIZE
    assert config.OLLAMA_MODEL
    assert config.EMBEDDING_MODEL
    assert config.SITEMAP_URL.startswith("https://www.onssa.gov.ma")


def test_paths_are_inside_data_dir():
    for path in (config.RAW_HTML_DIR, config.CLEAN_DIR, config.INDEX_DIR):
        assert config.DATA_DIR in path.parents
