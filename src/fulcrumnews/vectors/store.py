"""LanceDB vector store for article embeddings.

One table ``article_vectors``. The vector column width is fixed at create time to
``settings.embedding_dim``; we assert it matches on open (a dim mismatch is the
single highest-risk failure mode — see plan). Cosine distance is used throughout,
and vectors are expected to be L2-normalized before insert.
"""

from __future__ import annotations

import asyncio
import os
from dataclasses import dataclass
from datetime import datetime, timezone

import lancedb
import pyarrow as pa

from ..config import settings

_conn = None
_table = None
_lock = asyncio.Lock()


def _schema(dim: int) -> pa.Schema:
    return pa.schema(
        [
            ("id", pa.string()),  # == Article.lance_id
            ("vector", pa.list_(pa.float32(), dim)),
            ("article_id", pa.int64()),
            ("outlet", pa.string()),
            ("lean", pa.int8()),
            ("published_at", pa.int64()),  # epoch seconds
        ]
    )


def _epoch(dt: datetime | None) -> int:
    if dt is None:
        return 0
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return int(dt.timestamp())


@dataclass
class Match:
    article_id: int
    distance: float


async def get_table():
    """Open (or create) the vector table, asserting the stored dim matches config.

    Serialized with a lock and resilient to a create/open race: if ``create_table``
    reports the table already exists (stale listing or concurrent creator), we open it.
    """
    global _conn, _table
    if _table is not None:
        return _table

    async with _lock:
        if _table is not None:
            return _table

        os.makedirs(settings.lancedb_path, exist_ok=True)
        if _conn is None:
            _conn = await lancedb.connect_async(settings.lancedb_path)
        dim = settings.embedding_dim
        name = settings.lancedb_table

        table = None
        if name in await _conn.list_tables():
            table = await _conn.open_table(name)
        else:
            try:
                table = await _conn.create_table(name, schema=_schema(dim))
            except Exception:
                # Table appeared between the check and create — open it instead.
                table = await _conn.open_table(name)

        existing = (await table.schema()).field("vector").type.list_size
        if existing != dim:
            raise RuntimeError(
                f"LanceDB table '{name}' has vector dim {existing} but EMBEDDING_DIM={dim}. "
                f"Delete {settings.lancedb_path} (or change EMBEDDING_DIM back) to rebuild."
            )
        _table = table
        return _table


async def upsert(
    *, lance_id: str, vector: list[float], article_id: int, outlet: str, lean: int, published_at
) -> None:
    if len(vector) != settings.embedding_dim:
        raise ValueError(
            f"Embedding length {len(vector)} != EMBEDDING_DIM {settings.embedding_dim}"
        )
    table = await get_table()
    row = {
        "id": lance_id,
        "vector": vector,
        "article_id": article_id,
        "outlet": outlet,
        "lean": lean,
        "published_at": _epoch(published_at),
    }
    await (
        table.merge_insert("id")
        .when_matched_update_all()
        .when_not_matched_insert_all()
        .execute([row])
    )


async def nearest(
    vector: list[float],
    *,
    since: datetime | None = None,
    limit: int = 5,
    exclude_article_id: int | None = None,
) -> list[Match]:
    """Cosine nearest-neighbour search, optionally within a recency window."""
    table = await get_table()
    q = await table.search(vector)
    q = q.distance_type("cosine")
    clauses = []
    if since is not None:
        clauses.append(f"published_at >= {_epoch(since)}")
    if exclude_article_id is not None:
        clauses.append(f"article_id != {exclude_article_id}")
    if clauses:
        q = q.where(" AND ".join(clauses))
    rows = await q.limit(limit).to_list()
    return [Match(article_id=r["article_id"], distance=float(r["_distance"])) for r in rows]
