"""Story feed — the home page."""

from __future__ import annotations

from quart import Blueprint, current_app, redirect, render_template, request, url_for

from ...models import Story
from ...models.enums import BlindspotType
from ...scheduler import last_run, refresh_now

bp = Blueprint("feed", __name__)

PAGE_SIZE = 18
DEFAULT_MIN_SOURCES = 2


def _min_sources(args) -> int:
    try:
        return max(1, int(args.get("min", DEFAULT_MIN_SOURCES)))
    except (TypeError, ValueError):
        return DEFAULT_MIN_SOURCES


def _filtered_query(args):
    # Only show stories corroborated by at least `min` distinct outlets (default 2).
    qs = Story.filter(source_count__gte=_min_sources(args))
    lean = args.get("lean")
    if lean == "left":
        qs = qs.filter(left_count__gt=0)
    elif lean == "center":
        qs = qs.filter(center_count__gt=0)
    elif lean == "right":
        qs = qs.filter(right_count__gt=0)

    bs = args.get("blindspot")
    if bs == "left":
        qs = qs.filter(blindspot_type=BlindspotType.LEFT)
    elif bs == "right":
        qs = qs.filter(blindspot_type=BlindspotType.RIGHT)
    elif bs == "any":
        qs = qs.filter(blindspot_type__not=BlindspotType.NONE)

    q = (args.get("q") or "").strip()
    if q:
        qs = qs.filter(canonical_title__icontains=q)
    return qs


@bp.get("/")
@bp.get("/feed")
async def feed():
    args = request.args
    qs = _filtered_query(args)
    try:
        page = max(1, int(args.get("page", 1)))
    except ValueError:
        page = 1
    total = await qs.count()
    stories = (
        await qs.order_by("-updated_at").offset((page - 1) * PAGE_SIZE).limit(PAGE_SIZE)
    )
    return await render_template(
        "feed.html",
        stories=stories,
        page=page,
        has_next=page * PAGE_SIZE < total,
        total=total,
        filters=args,
        min_sources=_min_sources(args),
        last_run=last_run,
    )


@bp.post("/refresh")
async def refresh():
    """Reprocess all feeds in the background (single-flight). Triggerable from the feed."""
    current_app.add_background_task(refresh_now)
    return redirect(url_for("feed.feed", started=1))
