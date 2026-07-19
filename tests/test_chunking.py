"""Heading-aware chunking: sections, breadcrumbs, parent links, size bounds."""
from onssa_rag.chunking import split_page

DOC = {
    "url": "https://www.onssa.gov.ma/missions/",
    "title": "Missions de l'ONSSA",
    "section": "missions",
    "text": (
        "Intro avant les titres, présentation générale de l'office.\n\n"
        "## Surveillance\n" + ("Phrase sur la surveillance sanitaire du patrimoine végétal. " * 60)
        + "\n\n## Contrôle\nCourt paragraphe sur le contrôle."
    ),
}


def test_sections_split_on_headings():
    sections, _ = split_page(DOC, size=900, overlap=150)
    assert [s["heading"] for s in sections] == ["", "Surveillance", "Contrôle"]


def test_chunks_have_breadcrumb_and_valid_parent():
    sections, chunks = split_page(DOC, size=900, overlap=150)
    parent_ids = {s["parent_id"] for s in sections}
    assert chunks
    for chunk in chunks:
        assert chunk["parent_id"] in parent_ids
        assert chunk["text"].startswith("Missions de l'ONSSA")


def test_long_sections_are_split_with_bounded_size():
    _, chunks = split_page(DOC, size=900, overlap=150)
    surveillance = [c for c in chunks if c["heading"] == "Surveillance"]
    assert len(surveillance) >= 2
    assert all(len(c["text"]) <= 900 + 150 for c in chunks)  # body cap + breadcrumb


def test_page_without_headings_is_a_single_section():
    doc = dict(DOC, text="Texte simple sans titres. " * 10)
    sections, chunks = split_page(doc)
    assert len(sections) == 1
    assert sections[0]["heading"] == ""
    assert len(chunks) == 1
