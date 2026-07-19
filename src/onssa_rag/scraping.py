"""ONSSA website scraping: sitemap discovery, URL filtering, polite fetching.

The list of pages comes from data/pages.yaml (single source of truth):
sitemap URLs are expanded and filtered, `include` URLs are always kept,
`exclude` URLs and `exclude_patterns` always win.
"""
from __future__ import annotations

import hashlib
import re
import time
import xml.etree.ElementTree as ET
from pathlib import Path
from urllib.parse import unquote, urlparse

import requests
import yaml
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from . import config

SITEMAP_NS = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}


def load_pages_config(path: Path = config.PAGES_CONFIG) -> dict:
    with open(path, encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def make_session() -> requests.Session:
    session = requests.Session()
    session.headers["User-Agent"] = config.USER_AGENT
    retry = Retry(total=3, backoff_factor=1.5, status_forcelist=[429, 500, 502, 503, 504])
    session.mount("https://", HTTPAdapter(max_retries=retry))
    return session


def _sitemap_urls(session: requests.Session, sitemap_url: str) -> list[str]:
    resp = session.get(sitemap_url, timeout=30)
    resp.raise_for_status()
    root = ET.fromstring(resp.content)
    return [loc.text.strip() for loc in root.findall(".//sm:url/sm:loc", SITEMAP_NS) if loc.text]


def _is_french_url(url: str, filters: dict) -> bool:
    if filters.get("drop_query_langs") and "lang=" in url:
        return False
    if filters.get("drop_non_latin_slugs"):
        path = unquote(urlparse(url).path)
        if any(ord(ch) > 0x2FF for ch in path):
            return False
    return True


def discover_urls(pages_cfg: dict, session: requests.Session) -> list[str]:
    """Expand sitemaps, apply filters, merge include/exclude lists."""
    filters = pages_cfg.get("sitemap_filters", {})
    excludes = {e.rstrip("/") for e in pages_cfg.get("exclude", [])}
    patterns = [re.compile(p) for p in pages_cfg.get("exclude_patterns", [])]

    urls: set[str] = set(pages_cfg.get("include", []))
    for sitemap in pages_cfg.get("sitemaps", []):
        for url in _sitemap_urls(session, sitemap):
            if _is_french_url(url, filters):
                urls.add(url)

    def excluded(url: str) -> bool:
        return url.rstrip("/") in excludes or any(p.search(url) for p in patterns)

    return sorted(u for u in urls if not excluded(u))


def _cache_path(url: str) -> Path:
    digest = hashlib.sha1(url.encode()).hexdigest()[:16]
    slug = re.sub(r"[^a-z0-9]+", "-", urlparse(url).path.lower()).strip("-")[:60] or "accueil"
    return config.RAW_HTML_DIR / f"{slug}-{digest}.html"


def fetch_page(url: str, session: requests.Session, refresh: bool = False) -> str | None:
    """Return the page HTML, served from the local cache when available.

    The politeness delay only applies to real network hits, so re-runs of
    ingest.py never touch the website.
    """
    cache = _cache_path(url)
    if cache.exists() and not refresh:
        return cache.read_text(encoding="utf-8")
    try:
        resp = session.get(url, timeout=30)
        resp.raise_for_status()
    except requests.RequestException:
        return None
    finally:
        time.sleep(config.REQUEST_DELAY)
    cache.parent.mkdir(parents=True, exist_ok=True)
    cache.write_text(resp.text, encoding="utf-8")
    return resp.text
