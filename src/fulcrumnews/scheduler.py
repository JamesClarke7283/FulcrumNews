"""APScheduler-based periodic refresh, with single-flight protection."""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from .config import settings
from .graph.pipeline import run_pipeline

logger = logging.getLogger(__name__)

_scheduler: AsyncIOScheduler | None = None
_lock = asyncio.Lock()

# Lightweight run status for the admin dashboard.
last_run: dict = {"at": None, "stats": None, "running": False, "error": None}


async def refresh_now(window_hours: int | None = None) -> dict:
    """Run one pipeline pass unless one is already in flight (single-flight)."""
    if _lock.locked():
        logger.info("refresh skipped — a run is already in progress")
        return {"skipped": True}
    async with _lock:
        last_run["running"] = True
        last_run["error"] = None
        try:
            stats = await run_pipeline(window_hours)
            last_run["stats"] = stats
            last_run["at"] = datetime.now(timezone.utc).isoformat()
            return stats
        except Exception as e:  # noqa: BLE001
            logger.exception("pipeline run failed")
            last_run["error"] = f"{type(e).__name__}: {e}"
            return {"error": last_run["error"]}
        finally:
            last_run["running"] = False


def start_scheduler() -> None:
    global _scheduler
    if _scheduler is not None:
        return
    _scheduler = AsyncIOScheduler(timezone="UTC")
    interval = max(0.25, settings.refresh_interval_hours)
    _scheduler.add_job(
        refresh_now,
        "interval",
        hours=interval,
        id="refresh_news",
        max_instances=1,
        coalesce=True,
    )
    _scheduler.start()
    logger.info("scheduler started — refreshing every %.2f h", interval)


def stop_scheduler() -> None:
    global _scheduler
    if _scheduler is not None:
        _scheduler.shutdown(wait=False)
        _scheduler = None
