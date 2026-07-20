"""Speech text cleaning — pure function, no models needed."""
from onssa_rag.voice import clean_for_speech

ANSWER = (
    "Les **missions** de l'ONSSA sont multiples [1], [2] :\n"
    "- Surveillance sanitaire [1]\n"
    "- Contrôle des intrants agricoles\n"
    "Voir [la page missions](https://www.onssa.gov.ma/missions/) "
    "ou https://www.onssa.gov.ma/contact/ pour plus d'informations."
)


def test_citations_urls_and_markdown_removed():
    spoken = clean_for_speech(ANSWER)
    assert "[1]" not in spoken
    assert "https://" not in spoken
    assert "**" not in spoken
    assert "la page missions" in spoken  # link label kept, URL dropped
    assert "missions de l'ONSSA" in spoken
    assert "Surveillance sanitaire" in spoken


def test_accents_survive_cleaning():
    assert clean_for_speech("Sécurité **sanitaire** des aliments [3]") == (
        "Sécurité sanitaire des aliments"
    )
