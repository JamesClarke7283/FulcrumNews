"""The Outlet model — a news source. Fully runtime-editable via the admin UI."""

from __future__ import annotations

from tortoise import fields
from tortoise.models import Model

from .enums import FeedType, Lean


class Outlet(Model):
    id = fields.IntField(primary_key=True)
    name = fields.CharField(max_length=128)
    slug = fields.CharField(max_length=64, unique=True)
    lean = fields.IntEnumField(Lean, default=Lean.CENTER)
    feed_type = fields.IntEnumField(FeedType, default=FeedType.RSS)
    # RSS feed URL, or (for the Guardian) the API section query string.
    feed_url = fields.CharField(max_length=1024, default="")
    homepage = fields.CharField(max_length=512, null=True)
    enabled = fields.BooleanField(default=True)
    # Per-outlet knobs (e.g. Guardian section). Free-form.
    config = fields.JSONField(default=dict)
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)

    articles: fields.ReverseRelation["Article"]  # noqa: F821

    class Meta:
        table = "outlet"
        ordering = ["lean", "name"]

    def __str__(self) -> str:
        return f"{self.name} ({self.lean.slug})"
