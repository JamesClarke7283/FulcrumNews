"""The Story model — a cluster of articles from different outlets about one event."""

from __future__ import annotations

from tortoise import fields
from tortoise.models import Model

from .enums import BlindspotType


class Story(Model):
    id = fields.IntField(primary_key=True)
    slug = fields.CharField(max_length=96, unique=True)
    canonical_title = fields.CharField(max_length=512)

    # AI briefing (structured; produced by summarize node). Null until summarized.
    ai_summary = fields.TextField(null=True)
    ai_key_points = fields.JSONField(null=True)  # list[str]
    ai_differences = fields.JSONField(null=True)  # list[{outlet, angle}]
    ai_model = fields.CharField(max_length=128, null=True)
    summary_stale = fields.BooleanField(default=True)

    # Denormalized bias distribution (distinct outlets per bucket) for cheap feed render.
    blindspot_type = fields.IntEnumField(BlindspotType, default=BlindspotType.NONE)
    left_count = fields.IntField(default=0)
    center_count = fields.IntField(default=0)
    right_count = fields.IntField(default=0)
    source_count = fields.IntField(default=0)

    # Running-mean centroid vector (list[float]) for incremental matching.
    centroid = fields.JSONField(null=True)

    first_published_at = fields.DatetimeField(null=True)
    last_published_at = fields.DatetimeField(null=True)
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)

    articles: fields.ReverseRelation["Article"]  # noqa: F821

    class Meta:
        table = "story"
        ordering = ["-updated_at"]

    def __str__(self) -> str:
        return self.canonical_title
