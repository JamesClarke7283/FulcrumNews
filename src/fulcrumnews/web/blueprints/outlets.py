"""Public outlet roster + about/methodology page."""

from __future__ import annotations

from quart import Blueprint, render_template

from ...bias import bucket_of
from ...models import Outlet

bp = Blueprint("outlets", __name__)


@bp.get("/outlets")
async def list_outlets():
    outlets = await Outlet.all()
    groups: dict[str, list] = {"left": [], "center": [], "right": []}
    for o in outlets:
        groups[bucket_of(o.lean)].append(o)
    return await render_template("outlets.html", groups=groups)


@bp.get("/about")
async def about():
    return await render_template("about.html")
