"""LLM "format fixup": turn messy extracted article text into clean Markdown.

Trafilatura returns serviceable plaintext, but paragraph breaks, sub-headings and
lists are often lost. This asks the chat model to RE-FORMAT the text as Markdown
WITHOUT changing the wording — purely structural cleanup — for nicer rendering in
the per-outlet tabs.
"""

from __future__ import annotations

import logging
from functools import lru_cache

from langchain_openai import ChatOpenAI
from tenacity import retry, stop_after_attempt, wait_exponential

from ..config import settings

logger = logging.getLogger(__name__)

MAX_INPUT_CHARS = 16000

SYSTEM_PROMPT = (
    "You are a text formatter. You are given the raw extracted text of ONE news "
    "article. Re-format it as clean GitHub-flavored Markdown for readable display. "
    "STRICT RULES: do not add, remove, summarize, translate, or reword any content; "
    "preserve the original wording and order exactly. Only fix structure — split into "
    "paragraphs, add sub-headings (##) where the article clearly has sections, use "
    "blockquotes for pull quotes, and bullet lists where appropriate. Strip any "
    "leftover navigation, cookie/subscription notices, bylines repeated as noise, and "
    "'Read more' link cruft. Output ONLY the Markdown, with no preamble or code fences."
)


@lru_cache(maxsize=1)
def _format_model() -> ChatOpenAI:
    return ChatOpenAI(
        model=settings.chat_model,
        base_url=settings.openrouter_base_url,
        api_key=settings.openrouter_api_key,
        temperature=0,
        max_tokens=settings.format_max_tokens,
        timeout=settings.llm_timeout_s,
        default_headers={
            "HTTP-Referer": settings.openrouter_referer,
            "X-Title": "FulcrumNews",
        },
    )


def _strip_fences(text: str) -> str:
    t = text.strip()
    if t.startswith("```"):
        # remove an opening ```lang line and a trailing ```
        lines = t.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        t = "\n".join(lines)
    return t.strip()


@retry(stop=stop_after_attempt(3), wait=wait_exponential(min=2, max=20), reraise=True)
async def format_body(title: str, body: str) -> str:
    """Return cleaned Markdown for an article body. Falls back to the input on failure."""
    body = (body or "").strip()
    if not body:
        return ""
    model = _format_model()
    messages = [
        ("system", SYSTEM_PROMPT),
        ("human", f"# {title}\n\n{body[:MAX_INPUT_CHARS]}"),
    ]
    resp = await model.ainvoke(messages)
    content = resp.content if isinstance(resp.content, str) else str(resp.content)
    cleaned = _strip_fences(content)
    return cleaned or body
