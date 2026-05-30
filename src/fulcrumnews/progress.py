"""Shared, in-process progress state for the running pipeline.

Tracks three per-item phases separately — joining (clustering), summarizing, and
formatting — each with its own progress bar, plus a coarse status for the earlier
fetch/extract/embed steps. The web UI polls /api/progress to render the bars.
"""

from __future__ import annotations

TASK_KEYS = ("cluster", "summarize", "format")
TASK_LABELS = {
    "cluster": "Joining stories",
    "summarize": "Summarizing",
    "format": "Formatting articles",
}


def _empty_tasks() -> dict:
    return {k: {"label": TASK_LABELS[k], "done": 0, "total": 0, "current": ""} for k in TASK_KEYS}


_state: dict = {
    "running": False,
    "status": "idle",  # coarse status for fetch/extract/embed
    "tasks": _empty_tasks(),
    "stats": {},
    "error": None,
}


def _percent(done: int, total: int) -> int:
    return round(done / total * 100) if total else 0


def snapshot() -> dict:
    tasks = {}
    g_done = g_total = 0
    for key, t in _state["tasks"].items():
        tasks[key] = {**t, "percent": _percent(t["done"], t["total"])}
        g_done += t["done"]
        g_total += t["total"]
    return {
        "running": _state["running"],
        "status": _state["status"],
        "tasks": tasks,
        "global_percent": _percent(g_done, g_total) if g_total else (0 if _state["running"] else 100),
        "stats": _state["stats"],
        "error": _state["error"],
    }


def start() -> None:
    _state.update(running=True, status="Starting…", tasks=_empty_tasks(), stats={}, error=None)


def status(text: str) -> None:
    _state["status"] = text


def task_total(key: str, total: int) -> None:
    _state["tasks"][key].update(total=total, done=0, current="")


def task_step(key: str, current: str = "") -> None:
    t = _state["tasks"][key]
    t["done"] += 1
    if current:
        t["current"] = current


def finish(stats: dict | None = None, error: str | None = None) -> None:
    _state.update(running=False, status="Error" if error else "Done", stats=stats or {}, error=error)
