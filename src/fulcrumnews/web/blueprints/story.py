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
    # Order articles left → right by outlet lean.
    articles = sorted(story.articles, key=lambda a: int(a.outlet.lean))
    return await render_template("story.html", story=story, articles=articles)
