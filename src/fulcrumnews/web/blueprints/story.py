"""Story detail — AI briefing + per-outlet plaintext tabs."""

from __future__ import annotations

from quart import Blueprint, abort, render_template

from ...models import Story

bp = Blueprint("story", __name__)


@bp.get("/story/<slug>")
async def detail(slug: str):
    story = await Story.get_or_none(slug=slug).prefetch_related("articles__outlet")
    if story is None:
        abort(404)
    # One (richest-body) article per outlet, ordered left → right by lean — so an
    # outlet that published several articles on the story shows a single tab.
    by_outlet: dict[int, object] = {}
    for a in story.articles:
        cur = by_outlet.get(a.outlet_id)
        if cur is None or len(a.body or "") > len(cur.body or ""):
            by_outlet[a.outlet_id] = a
    articles = sorted(by_outlet.values(), key=lambda a: int(a.outlet.lean))
    return await render_template("story.html", story=story, articles=articles)
