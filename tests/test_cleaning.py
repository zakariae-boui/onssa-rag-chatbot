"""Content extraction: French text preserved, navigation hubs rejected."""
from onssa_rag.cleaning import extract_page

PARAGRAPH = (
    "L'ONSSA est chargé d'assurer la surveillance et la protection sanitaire "
    "du patrimoine végétal et animal au niveau national et aux frontières. "
)

ELEMENTOR_HTML = f"""
<html><head><title>Missions - ONSSA</title></head><body>
<header><nav>Accueil | Nos métiers | Réglementation</nav></header>
<h1>Missions de l'ONSSA</h1>
<div class="elementor-widget-container"><p>{PARAGRAPH * 5}</p></div>
<footer>contact@onssa.gov.ma</footer>
</body></html>
"""


def test_extracts_french_text_with_accents():
    doc = extract_page("https://www.onssa.gov.ma/missions/", ELEMENTOR_HTML)
    assert doc is not None
    assert "chargé" in doc["text"]
    assert "végétal" in doc["text"]
    assert doc["title"] == "Missions de l'ONSSA"
    assert doc["section"] == "missions"
    assert doc["url"].endswith("/missions/")


def test_navigation_hub_rejected():
    html = "<html><body><h1>ONSSA</h1><nav>Accueil Menu Contact</nav></body></html>"
    assert extract_page("https://www.onssa.gov.ma/onssa/", html) is None
