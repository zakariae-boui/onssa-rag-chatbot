"""Conversation store: roundtrip, titles, search — isolated in tmp_path."""
from onssa_rag import config
from onssa_rag import conversations as convs


def test_roundtrip_and_delete(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "DATA_DIR", tmp_path)
    conv = convs.create()
    convs.save(conv)  # empty conversations are not persisted
    assert convs.load_all() == []

    conv["messages"].append({"role": "user", "content": "Quelles sont les missions de l'ONSSA ?"})
    conv["title"] = convs.title_from(conv["messages"][0]["content"])
    convs.save(conv)
    loaded = convs.load_all()
    assert len(loaded) == 1
    assert loaded[0]["id"] == conv["id"]
    assert "missions" in loaded[0]["title"]

    convs.delete(conv["id"])
    assert convs.load_all() == []


def test_title_truncation():
    assert convs.title_from("") == "Nouvelle conversation"
    long_title = convs.title_from("mot " * 40)
    assert len(long_title) <= convs.TITLE_MAX + 1
    assert long_title.endswith("…")


def test_search_matches_title_and_content():
    a = convs.create()
    a["title"] = "Paiement électronique"
    a["messages"] = [{"role": "user", "content": "comment payer en ligne ?"}]
    b = convs.create()
    b["title"] = "Santé animale"
    b["messages"] = [{"role": "user", "content": "vaccination des bovins"}]

    assert convs.search([a, b], "paiement") == [a]
    assert convs.search([a, b], "bovins") == [b]
    assert convs.search([a, b], "") == [a, b]
