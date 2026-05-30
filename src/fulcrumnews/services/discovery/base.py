"""Shared discovery primitives: RawArticle, URL canonicalization, content hashing."""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

import httpx

from ...config import settings

_TRACKING_PARAM = re.compile(r"^(utm_|fb|gclid|mc_|ref_?$|igshid|cmp$|ito$|spm$)", re.IGNORECASE)


@dataclass
class RawArticle:
    outlet_slug: str
    url: str
    title: str
    author: str | None = None
    published_at: datetime | None = None
    snippet: str | None = None
    body: str | None = None
    extra: dict = field(default_factory=dict)


def canonicalize_url(url: str) -> str:
    """Normalize a URL for dedup: https, lowercase host, drop tracking params/fragment."""
    parts = urlsplit(url.strip())
    scheme = "https"
    netloc = parts.netloc.lower()
    if netloc.startswith("www."):
        netloc = netloc  # keep www; outlets are consistent within themselves
    query = [(k, v) for k, v in parse_qsl(parts.query) if not _TRACKING_PARAM.match(k)]
    path = parts.path.rstrip("/") or "/"
    return urlunsplit((scheme, netloc, path, urlencode(query), ""))


def content_hash(text: str | None) -> str | None:
    """sha256 of normalized body text (whitespace-collapsed, lowercased)."""
    if not text:
        return None
    normalized = re.sub(r"\s+", " ", text).strip().lower()
    if not normalized:
        return None
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def to_utc(dt: datetime | None) -> datetime | None:
    if dt is None:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def make_client() -> httpx.AsyncClient:
    return httpx.AsyncClient(
        headers={
            "User-Agent": settings.user_agent,
            # Bust intermediary/CDN caches so refreshes pull the freshest items.
            "Cache-Control": "no-cache, max-age=0",
            "Pragma": "no-cache",
        },
        timeout=settings.fetch_timeout_s,
        follow_redirects=True,
    )
