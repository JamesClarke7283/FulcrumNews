"""The Article model — one outlet's coverage of a story."""

from __future__ import annotations

from tortoise import fields
from tortoise.models import Model


class Article(Model):
    id = fields.IntField(primary_key=True)
    outlet = fields.ForeignKeyField(
        "models.Outlet", related_name="articles", on_delete=fields.CASCADE
    )
    story = fields.ForeignKeyField(
        "models.Story", related_name="articles", null=True, on_delete=fields.SET_NULL
    )
    url = fields.CharField(max_length=1024, unique=True)  # canonicalized
    title = fields.CharField(max_length=512)
    author = fields.CharField(max_length=256, null=True)
    body = fields.TextField(null=True)  # plaintext (Trafilatura / Guardian)
    body_md = fields.TextField(null=True)  # LLM-cleaned Markdown for display
    snippet = fields.CharField(max_length=1024, null=True)
    content_hash = fields.CharField(max_length=64, null=True, db_index=True)  # sha256(body)
    lance_id = fields.CharField(max_length=64, null=True, unique=True)  # LanceDB row id
    embedded = fields.BooleanField(default=False)
    published_at = fields.DatetimeField(null=True, db_index=True)
    fetched_at = fields.DatetimeField(auto_now_add=True)

    class Meta:
        table = "article"
        ordering = ["-published_at"]

    def __str__(self) -> str:
        return self.title
