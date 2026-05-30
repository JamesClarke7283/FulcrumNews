"""Dry-run feed verification for the admin "Verify feed" button.

Runs the SAME RSS path used at ingestion (fetch → feedparser → newest entry →
Trafilatura) so a green result reliably predicts a working outlet — without
writing anything to the database.
"""

from __future__ import annotations

import asyncio
import calendar
from dataclasses import asdict, dataclass
from datetime import datetime, timezone

import feedparser

from .base import make_client
from .rss import _extract


@dataclass
class VerifyResult:
    ok: bool
    message: str
    item_count: int = 0
    sample_titles: list[str] | None = None
    body_extracted: bool = False
    latest_published: str | None = None

    def to_dict(self) -> dict:
        d = asdict(self)
        d["sample_titles"] = self.sample_titles or []
        return d


async def verify_feed(feed_url: str) -> VerifyResult:
    feed_url = (feed_url or "").strip()
    if not feed_url.lower().startswith(("http://", "https://")):
        return VerifyResult(ok=False, message="Enter a valid http(s) RSS feed URL.")

    loop = asyncio.get_running_loop()
    async with make_client() as client:
        try:
            resp = await client.get(feed_url)
        except Exception as e:  # noqa: BLE001
            return VerifyResult(ok=False, message=f"Could not reach feed: {type(e).__name__}.")
        if resp.status_code != 200:
            return VerifyResult(ok=False, message=f"Feed returned HTTP {resp.status_code}.")

        parsed = await loop.run_in_executor(None, feedparser.parse, resp.content)
        entries = parsed.entries or []
        if not entries:
            return VerifyResult(ok=False, message="URL reachable but no RSS/Atom items found — is this a feed?")

        sample = [e.get("title", "(untitled)")[:120] for e in entries[:3]]
        latest = entries[0]
        latest_pub = None
        if latest.get("published_parsed"):
            try:
                latest_pub = datetime.fromtimestamp(
                    calendar.timegm(latest["published_parsed"]), tz=timezone.utc
                ).isoformat()
            except (OverflowError, ValueError):
                latest_pub = None

        # Confirm we can extract a body from the newest article.
        body_ok = False
        link = latest.get("link")
        if link:
            try:
                art = await client.get(link)
                if art.status_code == 200:
                    body = await loop.run_in_executor(None, _extract, art.text)
                    body_ok = bool(body and len(body) > 200)
            except Exception:  # noqa: BLE001
                body_ok = False

    msg = f"Feed OK — {len(entries)} items found."
    if not body_ok:
        msg += " (Headlines parse, but full-text extraction of the latest article was weak; the feed still works.)"
    return VerifyResult(
        ok=True,
        message=msg,
        item_count=len(entries),
        sample_titles=sample,
        body_extracted=body_ok,
        latest_published=latest_pub,
    )
