"""URL filtering logic — pure functions, no network."""
from onssa_rag.scraping import _cache_path, _is_french_url

FILTERS = {"drop_query_langs": True, "drop_non_latin_slugs": True}


def test_lang_param_dropped():
    assert not _is_french_url("https://www.onssa.gov.ma/organization/?lang=en", FILTERS)
    assert not _is_french_url("https://www.onssa.gov.ma/contact-new/?lang=ar", FILTERS)


def test_arabic_slug_dropped():
    url = "https://www.onssa.gov.ma/%D8%A7%D9%84%D8%B5%D8%AD%D8%A9-%D8%A7%D9%84%D9%86%D8%A8%D8%A7%D8%AA%D9%8A%D8%A9/"
    assert not _is_french_url(url, FILTERS)


def test_french_url_kept():
    assert _is_french_url("https://www.onssa.gov.ma/missions/", FILTERS)
    assert _is_french_url("https://www.onssa.gov.ma/controle-a-limportation-et-a-lexportation/", FILTERS)


def test_cache_path_is_stable_and_unique():
    a1 = _cache_path("https://www.onssa.gov.ma/missions/")
    a2 = _cache_path("https://www.onssa.gov.ma/missions/")
    b = _cache_path("https://www.onssa.gov.ma/reglementation/")
    assert a1 == a2
    assert a1 != b
    assert a1.suffix == ".html"
