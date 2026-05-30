"""Embedding generation via the OpenAI-compatible /embeddings endpoint."""

from __future__ import annotations

import logging
import math

from tenacity import retry, stop_after_attempt, wait_exponential

from ..config import settings
from .llm import get_embeddings_client

logger = logging.getLogger(__name__)

# Rough char budget per document (Qwen3 ~32k token context; we cap well under it).
MAX_CHARS = 8000
BATCH_SIZE = 32


def _l2_normalize(vec: list[float]) -> list[float]:
    norm = math.sqrt(sum(x * x for x in vec))
    if norm == 0:
        return vec
    return [x / norm for x in vec]


@retry(
    stop=stop_after_attempt(4),
    wait=wait_exponential(multiplier=1, min=2, max=30),
    reraise=True,
)
async def _embed_batch(texts: list[str]) -> list[list[float]]:
    client = get_embeddings_client()
    resp = await client.embeddings.create(model=settings.embedding_model, input=texts)
    return [d.embedding for d in resp.data]


async def embed_texts(texts: list[str]) -> list[list[float]]:
    """Embed texts → L2-normalized vectors. Asserts each matches EMBEDDING_DIM."""
    out: list[list[float]] = []
    for i in range(0, len(texts), BATCH_SIZE):
        batch = [(t or " ")[:MAX_CHARS] for t in texts[i : i + BATCH_SIZE]]
        vectors = await _embed_batch(batch)
        for v in vectors:
            if len(v) != settings.embedding_dim:
                raise RuntimeError(
                    f"Embedding model returned dim {len(v)} but EMBEDDING_DIM="
                    f"{settings.embedding_dim}. Update EMBEDDING_DIM (and rebuild the "
                    f"LanceDB table) to match {settings.embedding_model}."
                )
            out.append(_l2_normalize(v))
    return out


async def embed_text(text: str) -> list[list[float]]:
    return await embed_texts([text])
