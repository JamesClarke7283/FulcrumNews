"""The Guardian via the Open Platform content API (returns full body text)."""

from __future__ import annotations

import logging
from datetime import datetime

import httpx
from lxml import html as lxml_html
from tenacity import retry, stop_after_attempt, wait_exponential

from ...config import settings
from .base import RawArticle, canonicalize_url, to_utc

logger = logging.getLogger(__name__)

GUARDIAN_SEARCH = "https://content.guardianapis.com/search"


def _html_to_text(body_html: str) -> str:
    if not body_html:
        return ""
    try:
        doc = lxml_html.fromstring(body_html)
        return doc.text_content().strip()
    except Exception:  # noqa: BLE001
        return body_html


@retry(stop=stop_after_attempt(3), wait=wait_exponential(min=2, max=20), reraise=True)
async def _search(client: httpx.AsyncClient, section: str, page_size: int) -> dict:
    params = {
        "section": section,
        "show-fields": "body,byline,trailText",
        "order-by": "newest",
        "page-size": page_size,
        "api-key": settings.guardian_api_key,
    }
    resp = await client.get(GUARDIAN_SEARCH, params=params)
    resp.raise_for_status()
    return resp.json()


async def fetch_guardian(
    client: httpx.AsyncClient, outlet, *, page_size: int = 50
) -> list[RawArticle]:
    if not settings.guardian_api_key:
        logger.info("GUARDIAN_API_KEY not set — skipping Guardian outlet")
        return []

    section = (outlet.config or {}).get("section") or outlet.feed_url or "world"
    data = await _search(client, section, page_size)
    results = data.get("response", {}).get("results", [])

    articles: list[RawArticle] = []
    for r in results:
        fields = r.get("fields", {})
        body_text = _html_to_text(fields.get("body", ""))
        published = None
        if r.get("webPublicationDate"):
            published = to_utc(datetime.fromisoformat(r["webPublicationDate"].replace("Z", "+00:00")))
        articles.append(
            RawArticle(
                outlet_slug=outlet.slug,
                url=canonicalize_url(r["webUrl"]),
                title=r.get("webTitle", "")[:512],
                author=fields.get("byline"),
                published_at=published,
                snippet=(fields.get("trailText") or "")[:1024] or None,
                body=body_text or None,
            )
        )
    logger.info("Guardian: fetched %d articles (section=%s)", len(articles), section)
    return articles
