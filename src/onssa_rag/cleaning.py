"""Content extraction and cleaning for scraped ONSSA pages.

trafilatura does the heavy lifting (main-content extraction, boilerplate
removal); a BeautifulSoup pass over Elementor content containers is the
fallback for pages trafilatura cannot handle.
"""
from __future__ import annotations

import re
import unicodedata
from urllib.parse import unquote, urlparse

import trafilatura
from bs4 import BeautifulSoup

MIN_TEXT_CHARS = 200  # pages under this are navigation hubs, not content


def _normalize(text: str) -> str:
    text = unicodedata.normalize("NFC", text)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def _fallback_extract(html: str) -> str:
    soup = BeautifulSoup(html, "lxml")
    for tag in soup.select("header, footer, nav, script, style"):
        tag.decompose()
    blocks = [b.get_text(" ", strip=True) for b in soup.select(".elementor-widget-container")]
    return "\n\n".join(b for b in blocks if len(b) > 40)


def _title(html: str) -> str:
    soup = BeautifulSoup(html, "lxml")
    h1 = soup.find("h1")
    if h1 and h1.get_text(strip=True):
        return h1.get_text(strip=True)
    if soup.title and soup.title.string:
        return soup.title.string.split("-")[0].strip()
    return ""


def _section(url: str) -> str:
    parts = [p for p in unquote(urlparse(url).path).split("/") if p]
    return parts[0].replace("-", " ") if parts else "accueil"


def extract_page(url: str, html: str) -> dict | None:
    """Return a clean document dict, or None when the page has no real content."""
    text = trafilatura.extract(html, include_comments=False, include_tables=True) or ""
    if len(text) < MIN_TEXT_CHARS:
        text = _fallback_extract(html)
    text = _normalize(text)
    if len(text) < MIN_TEXT_CHARS:
        return None
    return {
        "url": url,
        "title": _normalize(_title(html)) or _section(url).title(),
        "section": _section(url),
        "text": text,
    }
