"""Tortoise ORM wiring: config, Quart registration, standalone init, and seeding."""

from __future__ import annotations

import logging
import os

from tortoise import Tortoise

from .config import settings
from .outlets import DEFAULT_OUTLET_ROSTER

logger = logging.getLogger(__name__)

MODELS = ["fulcrumnews.models"]


def _db_url() -> str:
    """SQLite connection string with WAL + foreign keys (concurrency safety)."""
    return f"{settings.db_url}?journal_mode=WAL&foreign_keys=ON"


TORTOISE_ORM = {
    "connections": {"default": _db_url()},
    "apps": {"models": {"models": MODELS, "default_connection": "default"}},
}


def _ensure_db_dir() -> None:
    db_dir = os.path.dirname(settings.sqlite_path)
    if db_dir:
        os.makedirs(db_dir, exist_ok=True)


async def _ensure_columns() -> None:
    """Add columns that ``generate_schemas(safe=True)`` won't add to existing tables.

    A tiny stand-in for migrations so an existing DB self-heals on startup.
    """
    conn = Tortoise.get_connection("default")
    expected = {"article": {"body_md": "TEXT"}}
    for table, cols in expected.items():
        existing = {r["name"] for r in await conn.execute_query_dict(f"PRAGMA table_info({table})")}
        for col, coltype in cols.items():
            if col not in existing:
                logger.info("Adding missing column %s.%s", table, col)
                await conn.execute_query(f"ALTER TABLE {table} ADD COLUMN {col} {coltype}")


async def init_db(*, generate_schemas: bool = True) -> None:
    """Initialize Tortoise standalone (CLI / pipeline runner).

    ``_enable_global_fallback`` lets queries run in tasks other than the one that
    called init() — required because the scheduler/pipeline run in background tasks.
    """
    _ensure_db_dir()
    await Tortoise.init(config=TORTOISE_ORM, _enable_global_fallback=True)
    if generate_schemas:
        await Tortoise.generate_schemas(safe=True)
        await _ensure_columns()


async def close_db() -> None:
    await Tortoise.close_connections()


def register_orm(app) -> None:
    """Attach Tortoise to a Quart app via before/after_serving hooks."""
    _ensure_db_dir()

    @app.before_serving
    async def _open_orm() -> None:
        # Global fallback: Quart runs before_serving in a background task, but request
        # handlers (and the scheduler) run in separate tasks — they need cross-task access.
        await Tortoise.init(config=TORTOISE_ORM, _enable_global_fallback=True)
        await Tortoise.generate_schemas(safe=True)
        await _ensure_columns()
        await seed_outlets()

    @app.after_serving
    async def _close_orm() -> None:
        await Tortoise.close_connections()


async def seed_outlets() -> int:
    """Insert the default roster on first run. Returns number created."""
    from .models import Outlet

    created = 0
    for spec in DEFAULT_OUTLET_ROSTER:
        _, was_created = await Outlet.get_or_create(
            slug=spec["slug"],
            defaults={
                "name": spec["name"],
                "lean": spec["lean"],
                "feed_type": spec["feed_type"],
                "feed_url": spec["feed_url"],
                "homepage": spec.get("homepage"),
                "enabled": spec.get("enabled", True),
                "config": spec.get("config", {}),
            },
        )
        created += int(was_created)
    if created:
        logger.info("Seeded %d outlets", created)
    return created
