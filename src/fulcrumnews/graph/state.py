"""Shared state for the LangGraph ingestion/analysis pipeline."""

from __future__ import annotations

import operator
from typing import Annotated, TypedDict


class PipelineState(TypedDict, total=False):
    window_hours: int
    new_article_ids: list[int]
    # article_id -> normalized embedding (this run only; not persisted in state)
    vectors: dict[int, list[float]]
    touched_story_ids: list[int]
    # Merged with `|` so parallel branches (summarize + format) can both update it.
    stats: Annotated[dict, operator.or_]
