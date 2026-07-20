"""Disk-persisted conversation store for the Streamlit app.

One JSON file per conversation under data/conversations/ (gitignored —
user chats are personal data and never belong in the repo).
"""
from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path

from . import config

TITLE_MAX = 45


def _dir() -> Path:
    path = config.DATA_DIR / "conversations"
    path.mkdir(parents=True, exist_ok=True)
    return path


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def title_from(text: str) -> str:
    text = " ".join(text.split())
    if not text:
        return "Nouvelle conversation"
    return text[:TITLE_MAX] + "…" if len(text) > TITLE_MAX else text


def create() -> dict:
    return {
        "id": f"{datetime.now(timezone.utc):%Y%m%d-%H%M%S}-{uuid.uuid4().hex[:6]}",
        "title": "Nouvelle conversation",
        "created_at": _now(),
        "updated_at": _now(),
        "messages": [],
    }


def save(conv: dict) -> None:
    """Persist a conversation; empty ones are never written to disk."""
    if not conv["messages"]:
        return
    conv["updated_at"] = _now()
    path = _dir() / f"{conv['id']}.json"
    path.write_text(json.dumps(conv, ensure_ascii=False, indent=1), encoding="utf-8")


def load_all() -> list[dict]:
    """All saved conversations, most recently updated first."""
    convs = []
    for path in _dir().glob("*.json"):
        try:
            convs.append(json.loads(path.read_text(encoding="utf-8")))
        except (json.JSONDecodeError, OSError):
            continue  # a corrupted file must not break the app
    return sorted(convs, key=lambda c: c.get("updated_at", ""), reverse=True)


def delete(conv_id: str) -> None:
    (_dir() / f"{conv_id}.json").unlink(missing_ok=True)


def search(convs: list[dict], query: str) -> list[dict]:
    """Filter conversations by title or message content (case-insensitive)."""
    q = query.strip().lower()
    if not q:
        return convs

    def matches(conv: dict) -> bool:
        if q in conv["title"].lower():
            return True
        return any(q in m["content"].lower() for m in conv["messages"])

    return [c for c in convs if matches(c)]
