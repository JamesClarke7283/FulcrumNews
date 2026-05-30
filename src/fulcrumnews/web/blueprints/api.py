"""JSON API."""

from __future__ import annotations

from quart import Blueprint, jsonify, request

from ...models import Story
from ...models.enums import BlindspotType
from .feed import PAGE_SIZE, _filtered_query

bp = Blueprint("api", __name__, url_prefix="/api")

_BLINDSPOT_SLUG = {BlindspotType.NONE: None, BlindspotType.LEFT: "left", BlindspotType.RIGHT: "right"}


def _story_brief(s: Story) -> dict:
    return {
        "id": s.id,
        "slug": s.slug,
        "title": s.canonical_title,
        "total_sources": s.source_count,
        "bias": {"left": s.left_count, "center": s.center_count, "right": s.right_count},
        "blindspot": _BLINDSPOT_SLUG[s.blindspot_type],
        "updated_at": s.updated_at.isoformat() if s.updated_at else None,
    }


@bp.get("/stories")
async def stories():
    qs = _filtered_query(request.args)
    try:
        page = max(1, int(request.args.get("page", 1)))
    except ValueError:
        page = 1
    total = await qs.count()
    rows = await qs.order_by("-updated_at").offset((page - 1) * PAGE_SIZE).limit(PAGE_SIZE)
    return jsonify(
        {
            "stories": [_story_brief(s) for s in rows],
            "page": page,
            "has_next": page * PAGE_SIZE < total,
            "total": total,
        }
    )


@bp.get("/stories/<int:story_id>")
async def story_detail(story_id: int):
    s = await Story.get_or_none(id=story_id).prefetch_related("articles__outlet")
    if s is None:
        return jsonify({"error": "not found"}), 404
    articles = sorted(s.articles, key=lambda a: int(a.outlet.lean))
    data = _story_brief(s)
    data.update(
        {
            "summary": s.ai_summary,
            "key_points": s.ai_key_points,
            "where_they_differ": s.ai_differences,
            "summary_model": s.ai_model,
            "articles": [
                {
                    "outlet": a.outlet.name,
                    "lean": a.outlet.lean.slug,
                    "title": a.title,
                    "url": a.url,
                    "published_at": a.published_at.isoformat() if a.published_at else None,
                    "body": a.body,
                }
                for a in articles
            ],
        }
    )
    return jsonify(data)
