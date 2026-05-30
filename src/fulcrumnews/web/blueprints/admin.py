"""Admin: manual refresh + runtime outlet management (RSS) with feed verification.

All routes are gated by ADMIN_TOKEN (if set). The token may be supplied via the
``token`` query/form field or the ``X-Admin-Token`` header. If ADMIN_TOKEN is empty
the admin area is open (DEV ONLY).
"""

from __future__ import annotations

import re
import uuid

from quart import (
    Blueprint,
    abort,
    current_app,
    jsonify,
    redirect,
    render_template,
    request,
    url_for,
)

from ...config import settings
from ...models import Outlet
from ...models.enums import FeedType, Lean
from ...scheduler import last_run, refresh_now
from ...services.discovery.verify import verify_feed

bp = Blueprint("admin", __name__, url_prefix="/admin")


@bp.before_request
async def _gate():
    if not settings.admin_token:
        return
    supplied = request.args.get("token") or request.headers.get("X-Admin-Token")
    if supplied is None and request.method in ("POST", "PUT", "DELETE"):
        form = await request.form
        supplied = form.get("token")
    if supplied != settings.admin_token:
        abort(401)


def _token_arg() -> dict:
    return {"token": settings.admin_token} if settings.admin_token else {}


async def _unique_slug(name: str, *, exclude_id: int | None = None) -> str:
    base = re.sub(r"[^a-z0-9]+", "-", (name or "outlet").lower()).strip("-")[:48] or "outlet"
    slug = base
    while True:
        existing = await Outlet.get_or_none(slug=slug)
        if existing is None or existing.id == exclude_id:
            return slug
        slug = f"{base}-{uuid.uuid4().hex[:4]}"


# ── Dashboard ────────────────────────────────────────────────────────────────
@bp.get("")
@bp.get("/")
async def dashboard():
    outlet_count = await Outlet.filter(enabled=True).count()
    return await render_template(
        "admin/dashboard.html",
        last_run=last_run,
        outlet_count=outlet_count,
        token=settings.admin_token,
    )


@bp.post("/refresh")
async def refresh():
    current_app.add_background_task(refresh_now)
    if request.headers.get("Accept", "").startswith("application/json"):
        return jsonify({"status": "started"}), 202
    return redirect(url_for("admin.dashboard", **_token_arg(), started=1))


# ── Outlet management ────────────────────────────────────────────────────────
@bp.get("/outlets")
async def outlets():
    rows = await Outlet.all()
    return await render_template(
        "admin/outlets.html", outlets=rows, token=settings.admin_token
    )


@bp.get("/outlets/new")
async def outlet_new():
    return await render_template(
        "admin/outlet_form.html",
        outlet=None,
        leans=list(Lean),
        token=settings.admin_token,
    )


@bp.get("/outlets/<slug>/edit")
async def outlet_edit(slug: str):
    outlet = await Outlet.get_or_none(slug=slug)
    if outlet is None:
        abort(404)
    return await render_template(
        "admin/outlet_form.html",
        outlet=outlet,
        leans=list(Lean),
        token=settings.admin_token,
    )


def _form_lean(form) -> Lean:
    try:
        return Lean(int(form.get("lean")))
    except (TypeError, ValueError):
        return Lean.CENTER


@bp.post("/outlets")
async def outlet_create():
    form = await request.form
    name = (form.get("name") or "").strip()
    feed_url = (form.get("feed_url") or "").strip()
    if not name or not feed_url:
        abort(400)
    await Outlet.create(
        name=name,
        slug=await _unique_slug(name),
        lean=_form_lean(form),
        feed_type=FeedType.RSS,
        feed_url=feed_url,
        homepage=(form.get("homepage") or "").strip() or None,
        enabled=form.get("enabled") == "on",
    )
    return redirect(url_for("admin.outlets", **_token_arg()))


@bp.post("/outlets/<slug>")
async def outlet_update(slug: str):
    outlet = await Outlet.get_or_none(slug=slug)
    if outlet is None:
        abort(404)
    form = await request.form
    outlet.name = (form.get("name") or outlet.name).strip()
    outlet.feed_url = (form.get("feed_url") or outlet.feed_url).strip()
    outlet.lean = _form_lean(form)
    outlet.homepage = (form.get("homepage") or "").strip() or None
    outlet.enabled = form.get("enabled") == "on"
    await outlet.save()
    return redirect(url_for("admin.outlets", **_token_arg()))


@bp.post("/outlets/<slug>/delete")
async def outlet_delete(slug: str):
    outlet = await Outlet.get_or_none(slug=slug)
    if outlet is not None:
        await outlet.delete()
    return redirect(url_for("admin.outlets", **_token_arg()))


@bp.post("/outlets/verify")
async def outlet_verify():
    if request.is_json:
        payload = await request.get_json()
        feed_url = (payload or {}).get("feed_url", "")
    else:
        form = await request.form
        feed_url = form.get("feed_url", "")
    result = await verify_feed(feed_url)
    return jsonify(result.to_dict())
