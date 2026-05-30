"""LangGraph StateGraph wiring for the ingestion/analysis pipeline.

    fetch_sources → extract_bodies → embed → cluster
        → assign_clusters → compute_bias_blindspot → summarize_cluster
"""

from __future__ import annotations

import logging
from functools import lru_cache

from langgraph.graph import END, START, StateGraph

from . import nodes
from .state import PipelineState

logger = logging.getLogger(__name__)


@lru_cache(maxsize=1)
def build_pipeline():
    g = StateGraph(PipelineState)
    g.add_node("fetch_sources", nodes.fetch_sources)
    g.add_node("extract_bodies", nodes.extract_bodies)
    g.add_node("embed", nodes.embed)
    g.add_node("cluster", nodes.cluster)
    g.add_node("assign_clusters", nodes.assign_clusters)
    g.add_node("compute_bias_blindspot", nodes.compute_bias_blindspot)
    g.add_node("summarize_cluster", nodes.summarize_cluster)
    g.add_node("format_bodies", nodes.format_bodies)

    g.add_edge(START, "fetch_sources")
    g.add_edge("fetch_sources", "extract_bodies")
    g.add_edge("extract_bodies", "embed")
    g.add_edge("embed", "cluster")
    g.add_edge("cluster", "assign_clusters")
    g.add_edge("assign_clusters", "compute_bias_blindspot")
    # Summarizing and formatting are independent → run them concurrently.
    g.add_edge("compute_bias_blindspot", "summarize_cluster")
    g.add_edge("compute_bias_blindspot", "format_bodies")
    g.add_edge("summarize_cluster", END)
    g.add_edge("format_bodies", END)
    return g.compile()


async def run_pipeline(window_hours: int | None = None) -> dict:
    """Invoke one full pipeline pass. Returns the run stats."""
    from .. import runtime

    graph = build_pipeline()
    initial: PipelineState = {
        "window_hours": window_hours or runtime.get_window_hours(),
        "new_article_ids": [],
        "vectors": {},
        "touched_story_ids": [],
        "stats": {},
    }
    result = await graph.ainvoke(initial)
    return result.get("stats", {})


async def _main() -> None:
    import logging as _logging

    from ..config import settings
    from ..db import close_db, init_db, seed_outlets

    _logging.basicConfig(
        level=settings.log_level,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    await init_db()
    await seed_outlets()
    try:
        stats = await run_pipeline()
        logger.info("Pipeline finished: %s", stats)
    finally:
        await close_db()


def main() -> None:
    import asyncio

    asyncio.run(_main())


if __name__ == "__main__":
    main()
