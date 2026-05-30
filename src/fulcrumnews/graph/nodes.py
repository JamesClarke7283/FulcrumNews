"""The seven async pipeline nodes. Each delegates to a service and returns a
partial state update. Stats are accumulated by merging on each node."""

from __future__ import annotations

import asyncio
import logging
import re
import uuid
from datetime import datetime, timedelta, timezone

from ..bias import compute_bias
from ..config import settings
from ..models import Article, Lean, Outlet, Story
from ..models.enums import FeedType
from ..services import summarize
from ..services.discovery import guardian, rss
from ..services.discovery.base import content_hash, make_client
from ..services.embeddings import embed_texts
from ..vectors import store
from .state import PipelineState

logger = logging.getLogger(__name__)


def _merge_stats(state: PipelineState, **kw) -> dict:
    stats = dict(state.get("stats") or {})
    stats.update(kw)
    return stats


def _slugify(title: str) -> str:
    base = re.sub(r"[^a-z0-9]+", "-", (title or "story").lower()).strip("-")[:72]
    return f"{base or 'story'}-{uuid.uuid4().hex[:6]}"


_STOPWORDS = {
    "the", "and", "for", "with", "from", "that", "this", "after", "over", "into",
    "amid", "says", "say", "said", "will", "have", "has", "was", "were", "are",
    "but", "not", "new", "how", "why", "what", "who", "when", "where", "his", "her",
    "their", "they", "you", "your", "our", "out", "off", "down", "more", "than",
    "been", "being", "could", "would", "should", "about", "against", "amid",
    "first", "last", "year", "years", "day", "days", "week", "uk", "live", "watch",
}


def _title_tokens(title: str) -> set[str]:
    """Significant lowercased tokens from a headline (entities/keywords)."""
    toks = re.findall(r"[a-z0-9]+", (title or "").lower())
    return {t for t in toks if len(t) > 3 and t not in _STOPWORDS}


def _embed_text(article: Article) -> str:
    """Text used for SAME-EVENT clustering.

    We use the title plus the lead (snippet, or the first ~600 chars of the body),
    not the full body: leads summarize the event, so two outlets covering the same
    event have very similar leads, while full bodies diverge in length and detail.
    """
    lead = article.snippet or (article.body or "")[:600]
    title = article.title or ""
    # Weight the title (it carries the strongest same-event signal).
    return f"{title}\n{title}\n{lead}".strip()


# ── 1. fetch_sources ─────────────────────────────────────────────────────────
async def fetch_sources(state: PipelineState) -> PipelineState:
    outlets = await Outlet.filter(enabled=True)
    new_ids: list[int] = []
    fetched = 0

    async with make_client() as client:
        async def fetch_one(outlet: Outlet):
            if outlet.feed_type == FeedType.GUARDIAN_API:
                return await guardian.fetch_guardian(client, outlet)
            return await rss.fetch_rss(client, outlet)

        results = await asyncio.gather(
            *(fetch_one(o) for o in outlets), return_exceptions=True
        )

    outlet_by_slug = {o.slug: o for o in outlets}
    for res in results:
        if isinstance(res, Exception):
            logger.warning("source fetch error: %s", res)
            continue
        for raw in res:
            fetched += 1
            outlet = outlet_by_slug.get(raw.outlet_slug)
            if outlet is None:
                continue
            article, created = await Article.get_or_create(
                url=raw.url,
                defaults={
                    "outlet_id": outlet.id,
                    "title": raw.title,
                    "author": raw.author,
                    "body": raw.body,
                    "snippet": raw.snippet,
                    "content_hash": content_hash(raw.body),
                    "published_at": raw.published_at,
                },
            )
            if created:
                new_ids.append(article.id)

    logger.info("fetch_sources: %d fetched, %d new", fetched, len(new_ids))
    return {
        "new_article_ids": new_ids,
        "stats": _merge_stats(state, fetched=fetched, new=len(new_ids)),
    }


# ── 2. extract_bodies ────────────────────────────────────────────────────────
async def extract_bodies(state: PipelineState) -> PipelineState:
    ids = state.get("new_article_ids") or []
    articles = await Article.filter(id__in=ids, body__isnull=True)
    if not articles:
        return {"stats": _merge_stats(state, extracted=0)}

    sem = asyncio.Semaphore(settings.fetch_concurrency)
    extracted = 0

    async with make_client() as client:
        async def do(article: Article):
            nonlocal extracted
            async with sem:
                body = await rss.extract_body(client, article.url)
            if body:
                article.body = body
                article.content_hash = content_hash(body)
                if not article.snippet:
                    article.snippet = body[:1024]
                await article.save(update_fields=["body", "content_hash", "snippet"])
                extracted += 1

        await asyncio.gather(*(do(a) for a in articles))

    logger.info("extract_bodies: %d bodies extracted", extracted)
    return {"stats": _merge_stats(state, extracted=extracted)}


# ── 3. embed ─────────────────────────────────────────────────────────────────
async def embed(state: PipelineState) -> PipelineState:
    ids = state.get("new_article_ids") or []
    articles = await Article.filter(id__in=ids, embedded=False)
    articles = [a for a in articles if (a.body or a.snippet or a.title)]
    if not articles:
        return {"vectors": {}, "stats": _merge_stats(state, embedded=0)}

    texts = [_embed_text(a) for a in articles]
    vectors = await embed_texts(texts)

    out: dict[int, list[float]] = {}
    for article, vec in zip(articles, vectors, strict=True):
        lance_id = article.lance_id or uuid.uuid4().hex
        await store.upsert(
            lance_id=lance_id,
            vector=vec,
            article_id=article.id,
            outlet=str(article.outlet_id),
            lean=0,
            published_at=article.published_at,
        )
        article.lance_id = lance_id
        article.embedded = True
        await article.save(update_fields=["lance_id", "embedded"])
        out[article.id] = vec

    logger.info("embed: %d articles embedded", len(out))
    return {"vectors": out, "stats": _merge_stats(state, embedded=len(out))}


# ── 4. cluster ───────────────────────────────────────────────────────────────
async def cluster(state: PipelineState) -> PipelineState:
    vectors = state.get("vectors") or {}
    if not vectors:
        return {"touched_story_ids": [], "stats": _merge_stats(state, clustered=0)}

    loose = settings.cluster_distance_threshold
    strict = settings.cluster_strict_distance
    min_overlap = settings.cluster_min_title_overlap
    cutoff = datetime.now(timezone.utc) - timedelta(hours=settings.cluster_window_hours)

    # Process oldest-first so a developing story's earliest article anchors the cluster.
    articles = await Article.filter(id__in=list(vectors.keys())).order_by("published_at")
    assigned: dict[int, int] = {}  # article_id -> story_id (this batch)
    token_cache: dict[int, set[str]] = {}  # article_id -> significant title tokens
    touched: set[int] = set()

    async def candidate_info(aid: int) -> tuple[int | None, set[str]]:
        """(story_id, title_tokens) for a candidate article id, cached."""
        sid = assigned.get(aid)
        toks = token_cache.get(aid)
        if sid is not None and toks is not None:
            return sid, toks
        row = await Article.filter(id=aid).values("story_id", "title")
        if not row:
            return None, set()
        sid = assigned.get(aid, row[0]["story_id"])
        toks = _title_tokens(row[0]["title"])
        token_cache[aid] = toks
        return sid, toks

    for article in articles:
        vec = vectors[article.id]
        my_tokens = _title_tokens(article.title)
        token_cache[article.id] = my_tokens
        matches = await store.nearest(
            vec, since=cutoff, limit=12, exclude_article_id=article.id
        )
        story_id = None
        for m in matches:
            if m.distance > loose:
                break  # results are sorted nearest-first
            sid, cand_tokens = await candidate_info(m.article_id)
            if not sid:
                continue
            # Strict band: embeddings clearly match. Loose band: require shared keywords.
            if m.distance <= strict or len(my_tokens & cand_tokens) >= min_overlap:
                story_id = sid
                break

        if story_id is None:
            story = await Story.create(
                slug=_slugify(article.title),
                canonical_title=article.title,
                summary_stale=True,
            )
            story_id = story.id

        article.story_id = story_id
        await article.save(update_fields=["story_id"])
        assigned[article.id] = story_id
        touched.add(story_id)

    logger.info("cluster: %d articles into %d stories", len(articles), len(touched))
    return {
        "touched_story_ids": sorted(touched),
        "stats": _merge_stats(state, clustered=len(articles), stories_touched=len(touched)),
    }


# ── 5. assign_clusters (recompute story aggregates) ──────────────────────────
async def assign_clusters(state: PipelineState) -> PipelineState:
    story_ids = state.get("touched_story_ids") or []
    for sid in story_ids:
        story = await Story.get_or_none(id=sid)
        if story is None:
            continue
        arts = await Article.filter(story_id=sid).order_by("-published_at")
        if not arts:
            continue
        distinct_outlets = {a.outlet_id for a in arts}
        pubs = [a.published_at for a in arts if a.published_at]
        story.source_count = len(distinct_outlets)
        story.first_published_at = min(pubs) if pubs else None
        story.last_published_at = max(pubs) if pubs else None
        story.canonical_title = arts[0].title  # most recent headline
        story.summary_stale = True
        await story.save(
            update_fields=[
                "source_count",
                "first_published_at",
                "last_published_at",
                "canonical_title",
                "summary_stale",
            ]
        )
    return {"stats": _merge_stats(state)}


# ── 6. compute_bias_blindspot ────────────────────────────────────────────────
async def compute_bias_blindspot(state: PipelineState) -> PipelineState:
    story_ids = state.get("touched_story_ids") or []
    for sid in story_ids:
        rows = await Article.filter(story_id=sid).values("outlet_id", "outlet__lean")
        # one lean per distinct outlet
        outlet_lean: dict[int, Lean] = {}
        for r in rows:
            outlet_lean[r["outlet_id"]] = Lean(r["outlet__lean"])
        result = compute_bias(
            outlet_lean.values(),
            min_sources=settings.blindspot_min_sources,
            min_share=settings.blindspot_min_share,
        )
        await Story.filter(id=sid).update(
            left_count=result.left,
            center_count=result.center,
            right_count=result.right,
            blindspot_type=result.blindspot,
        )
    return {"stats": _merge_stats(state)}


# ── 7. summarize_cluster ─────────────────────────────────────────────────────
async def summarize_cluster(state: PipelineState) -> PipelineState:
    story_ids = state.get("touched_story_ids") or []
    summarized = 0

    # Bound cost/time: summarize the most-corroborated stale stories first, up to a cap.
    candidates = await Story.filter(
        id__in=story_ids, summary_stale=True, source_count__gte=2
    ).order_by("-source_count")
    candidates = candidates[: settings.max_summaries_per_run]

    for story in candidates:
        sid = story.id
        arts = await Article.filter(story_id=sid).prefetch_related("outlet")
        # one (richest) article per outlet to avoid syndication double-counting
        by_outlet: dict[int, Article] = {}
        for a in arts:
            cur = by_outlet.get(a.outlet_id)
            if cur is None or len(a.body or "") > len(cur.body or ""):
                by_outlet[a.outlet_id] = a

        inputs = [
            summarize.ArticleInput(
                outlet_name=a.outlet.name,
                lean_label=a.outlet.lean.label,
                body=a.body or a.snippet or a.title,
            )
            for a in by_outlet.values()
        ]
        try:
            briefing = await summarize.summarize_story(story.canonical_title, inputs)
        except Exception as e:  # noqa: BLE001
            logger.warning("summarize failed for story %s: %s", sid, e)
            continue

        story.ai_summary = briefing.summary
        story.ai_key_points = briefing.key_points
        story.ai_differences = briefing.where_they_differ
        story.ai_model = summarize.model_name()
        story.summary_stale = False
        await story.save(
            update_fields=[
                "ai_summary",
                "ai_key_points",
                "ai_differences",
                "ai_model",
                "summary_stale",
            ]
        )
        summarized += 1

    logger.info("summarize_cluster: %d stories summarized", summarized)
    return {"stats": _merge_stats(state, summarized=summarized)}
