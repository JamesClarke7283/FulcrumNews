"""LLM + embeddings clients pointed at OpenRouter (OpenAI-compatible)."""

from __future__ import annotations

from functools import lru_cache

from langchain_openai import ChatOpenAI
from openai import AsyncOpenAI

from ..config import settings


@lru_cache(maxsize=1)
def get_chat_model() -> ChatOpenAI:
    """Kimi (or configured CHAT_MODEL) via OpenRouter for the AI briefing."""
    return ChatOpenAI(
        model=settings.chat_model,
        base_url=settings.openrouter_base_url,
        api_key=settings.openrouter_api_key,
        temperature=settings.summary_temperature,
        max_tokens=settings.summary_max_tokens,
        timeout=settings.llm_timeout_s,
        default_headers={
            "HTTP-Referer": settings.openrouter_referer,
            "X-Title": "FulcrumNews",
        },
    )


@lru_cache(maxsize=1)
def get_embeddings_client() -> AsyncOpenAI:
    """Raw OpenAI-compatible client for the /embeddings endpoint.

    Used directly (not via LangChain's OpenAIEmbeddings) to avoid its tiktoken-based
    context chunking, which is wrong for non-OpenAI models like Qwen.
    """
    return AsyncOpenAI(
        base_url=settings.resolved_embeddings_base_url(),
        api_key=settings.resolved_embeddings_api_key(),
        timeout=settings.llm_timeout_s,
    )
