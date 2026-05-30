"""Jinja template filters/globals for FulcrumNews."""

from __future__ import annotations

from datetime import datetime, timezone

import markdown as _markdown
import nh3
from markupsafe import Markup, escape

from ..bias import bucket_of
from ..models.enums import Lean


def _bucket(value) -> str:
    try:
        return bucket_of(Lean(int(value)))
    except (ValueError, TypeError):
        return "center"


def _pct(part: int, total: int) -> int:
    if not total:
        return 0
    return round(part / total * 100)


def _lean_label(value) -> str:
    try:
        return Lean(int(value)).label
    except (ValueError, TypeError):
        return str(value)


def _timeago(dt: datetime | None) -> str:
    if not dt:
        return ""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    delta = datetime.now(timezone.utc) - dt
    secs = int(delta.total_seconds())
    if secs < 60:
        return "just now"
    if secs < 3600:
        return f"{secs // 60}m ago"
    if secs < 86400:
        return f"{secs // 3600}h ago"
    days = secs // 86400
    return f"{days}d ago" if days < 7 else dt.strftime("%d %b %Y")


_MD_TAGS = {
    "p", "br", "strong", "em", "b", "i", "u", "blockquote", "h2", "h3", "h4",
    "ul", "ol", "li", "a", "code", "pre", "hr", "span",
}


def _markdown_html(text: str | None) -> Markup:
    """Render Markdown → sanitized HTML (for LLM-formatted article bodies)."""
    if not text:
        return Markup("")
    html = _markdown.markdown(str(text), extensions=["extra", "sane_lists"])
    # nh3 manages link rel safety itself (default rel="noopener noreferrer").
    clean = nh3.clean(html, tags=_MD_TAGS, attributes={"a": {"href", "title"}})
    return Markup(clean)


def _nl2br(text: str | None) -> Markup:
    if not text:
        return Markup("")
    paragraphs = [p.strip() for p in str(text).split("\n") if p.strip()]
    return Markup("".join(f"<p>{escape(p)}</p>" for p in paragraphs))


def register_filters(app) -> None:
    app.jinja_env.filters["pct"] = _pct
    app.jinja_env.filters["bucket"] = _bucket
    app.jinja_env.filters["lean_label"] = _lean_label
    app.jinja_env.filters["timeago"] = _timeago
    app.jinja_env.filters["nl2br"] = _nl2br
    app.jinja_env.filters["markdown"] = _markdown_html
