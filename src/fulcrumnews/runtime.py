"""Runtime-adjustable settings, changeable from the admin panel and persisted to disk.

Pydantic settings are immutable env config; this holds the few values an operator can
tweak at runtime (currently the clustering/exploration window).
"""

from __future__ import annotations

import json
import os

from .config import settings

_PATH = os.path.join(os.path.dirname(settings.sqlite_path) or ".", "runtime.json")
_state = {"cluster_window_hours": settings.cluster_window_hours}


def _save() -> None:
    try:
        os.makedirs(os.path.dirname(_PATH) or ".", exist_ok=True)
        with open(_PATH, "w") as f:
            json.dump(_state, f)
    except OSError:
        pass


def _load() -> None:
    try:
        with open(_PATH) as f:
            data = json.load(f)
        h = data.get("cluster_window_hours")
        if isinstance(h, int):
            _state["cluster_window_hours"] = h
    except (FileNotFoundError, ValueError, OSError):
        pass


def get_window_hours() -> int:
    return _state["cluster_window_hours"]


def get_window_days() -> int:
    return round(_state["cluster_window_hours"] / 24)


def set_window_days(days: float) -> int:
    """Set the clustering window in days (clamped 1 .. max). Returns hours."""
    max_h = settings.cluster_max_window_hours
    hours = max(24, min(int(round(float(days) * 24)), max_h))
    _state["cluster_window_hours"] = hours
    _save()
    return hours


_load()
