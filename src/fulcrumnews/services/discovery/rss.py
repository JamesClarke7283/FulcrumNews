"""RSS discovery (feedparser) + full-text extraction (Trafilatura).

Both feedparser and trafilatura are blocking/CPU-bound, so they run in the default
thread-pool executor to avoid stalling the event loop.
"""

from __future__ import annotations

import asyncio
import calendar
import logging
import re
from datetime import datetime, timezone

import feedparser
import httpx
import trafilatura

from .base import RawArticle, canonicalize_url

logger = logging.getLogger(__name__)

_TAG_RE = re.compile(r"<[^>]+>")


def _struct_to_dt(parsed) -> datetime | None:
    if not parsed:
        return None
    try:
        return datetime.fromtimestamp(calendar.timegm(parsed), tz=timezone.utc)
    except (OverflowError, ValueError):
        return None


def _clean_summary(text: str | None) -> str | None:
    if not text:
        return None
    stripped = _TAG_RE.sub("", text).strip()
    return stripped[:1024] or None


async def fetch_rss(client: httpx.AsyncClient, outlet, *, limit: int | None = None) -> list[RawArticle]:
    """Fetch + parse an RSS/Atom feed. Bodies are filled later by extract_body()."""
    from ...config import settings

    if limit is None:
        limit = settings.rss_max_items
    loop = asyncio.get_running_loop()
    try:
        resp = await client.get(outlet.feed_url)
        resp.raise_for_status()
    except Exception as e:  # noqa: BLE001
        logger.warning("RSS fetch failed for %s (%s): %s", outlet.slug, outlet.feed_url, e)
        return []

    parsed = await loop.run_in_executor(None, feedparser.parse, resp.content)
    articles: list[RawArticle] = []
    for entry in parsed.entries[:limit]:
        link = entry.get("link")
        title = entry.get("title")
        if not link or not title:
            continue
        articles.append(
            RawArticle(
                outlet_slug=outlet.slug,
                url=canonicalize_url(link),
                title=title[:512],
                author=entry.get("author"),
                published_at=_struct_to_dt(entry.get("published_parsed"))
                or _struct_to_dt(entry.get("updated_parsed")),
                snippet=_clean_summary(entry.get("summary")),
            )
        )
    logger.info("RSS %s: parsed %d entries", outlet.slug, len(articles))
    return articles


def _extract(html: str) -> str | None:
    return trafilatura.extract(
        html, include_comments=False, include_tables=False, favor_precision=True
    )


async def extract_body(client: httpx.AsyncClient, url: str) -> str | None:
    """Fetch an article page and extract plaintext body with Trafilatura."""
    loop = asyncio.get_running_loop()
    try:
        resp = await client.get(url)
        resp.raise_for_status()
    except Exception as e:  # noqa: BLE001
        logger.debug("body fetch failed %s: %s", url, e)
        return None
    return await loop.run_in_executor(None, _extract, resp.text)
