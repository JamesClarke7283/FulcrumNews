"""Shared state for the LangGraph ingestion/analysis pipeline."""

from __future__ import annotations

from typing import TypedDict


class PipelineState(TypedDict, total=False):
    window_hours: int
    new_article_ids: list[int]
    # article_id -> normalized embedding (this run only; not persisted in state)
    vectors: dict[int, list[float]]
    touched_story_ids: list[int]
    stats: dict
