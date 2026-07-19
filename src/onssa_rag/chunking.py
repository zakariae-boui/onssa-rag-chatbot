"""Heading-aware chunking: markdown sections -> overlapping chunks.

Each chunk carries a breadcrumb prefix ("Page title › Section heading") so it
stays self-describing after retrieval, and a parent_id so the runtime can
expand a winning chunk to its full parent section (small-to-big retrieval).
"""
from __future__ import annotations

import hashlib
import re

from . import config

HEADING_RE = re.compile(r"^#{1,6}\s+(.*)$")


def _page_key(url: str) -> str:
    return hashlib.sha1(url.encode()).hexdigest()[:8]


def _split_sections(text: str) -> list[tuple[str, str]]:
    """Split markdown text into (heading, body) pairs; intro text gets heading ''."""
    sections: list[tuple[str, str]] = []
    heading, buf = "", []
    for line in text.splitlines():
        match = HEADING_RE.match(line)
        if match:
            if "\n".join(buf).strip():
                sections.append((heading, "\n".join(buf).strip()))
            heading, buf = match.group(1).strip(), []
        else:
            buf.append(line)
    if "\n".join(buf).strip():
        sections.append((heading, "\n".join(buf).strip()))
    return sections


def _split_long(text: str, size: int, overlap: int) -> list[str]:
    """Greedy paragraph/sentence packing into ~size chars, word-boundary overlap."""
    pieces: list[str] = []
    for para in re.split(r"\n{2,}", text):
        if len(para) <= size:
            pieces.append(para)
        else:
            pieces.extend(re.split(r"(?<=[.!?;]) +", para))

    chunks: list[str] = []
    cur = ""
    for piece in pieces:
        piece = piece.strip()
        if not piece:
            continue
        while len(piece) > size:  # pathological sentence longer than a whole chunk
            chunks.append(piece[:size])
            piece = piece[size - overlap:]
        if cur and len(cur) + len(piece) + 2 > size:
            chunks.append(cur)
            tail = cur[-overlap:]
            tail = tail[tail.find(" ") + 1:] if " " in tail else tail
            cur = f"{tail} {piece}".strip()
        else:
            cur = f"{cur}\n\n{piece}" if cur else piece
    if cur:
        chunks.append(cur)
    return chunks


def split_page(
    doc: dict,
    size: int = config.CHUNK_SIZE,
    overlap: int = config.CHUNK_OVERLAP,
) -> tuple[list[dict], list[dict]]:
    """Return (sections, chunks) for one cleaned page document."""
    key = _page_key(doc["url"])
    sections: list[dict] = []
    chunks: list[dict] = []
    for s_idx, (heading, body) in enumerate(_split_sections(doc["text"])):
        parent_id = f"{key}-s{s_idx}"
        sections.append(
            {
                "parent_id": parent_id,
                "url": doc["url"],
                "title": doc["title"],
                "heading": heading,
                "text": body,
            }
        )
        breadcrumb = " › ".join(x for x in (doc["title"], heading) if x)
        for c_idx, piece in enumerate(_split_long(body, size, overlap)):
            chunks.append(
                {
                    "chunk_id": f"{parent_id}-c{c_idx}",
                    "parent_id": parent_id,
                    "url": doc["url"],
                    "title": doc["title"],
                    "section": doc["section"],
                    "heading": heading,
                    "text": f"{breadcrumb}\n{piece}",
                }
            )
    return sections, chunks
