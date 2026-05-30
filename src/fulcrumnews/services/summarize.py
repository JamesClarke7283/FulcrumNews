"""Neutral cross-outlet AI briefing via the chat model (Kimi by default).

We prompt for strict JSON and parse defensively rather than relying on a specific
provider's tool-calling/JSON-mode support through OpenRouter.
"""

from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass

from tenacity import retry, stop_after_attempt, wait_exponential

from ..config import settings
from .llm import get_chat_model

logger = logging.getLogger(__name__)

PER_OUTLET_CHARS = 3500
MAX_OUTLETS = 12

SYSTEM_PROMPT = (
    "You are a neutral news analyst. You summarize how multiple outlets across the "
    "political spectrum cover ONE story. Be strictly factual and non-partisan; never "
    "adopt any single outlet's framing as truth. Respond with JSON ONLY, no prose, no "
    "code fences."
)

USER_TEMPLATE = """Story working title: {title}

Below are articles from {n} outlets, each tagged with its political lean. Identify the
shared factual core and where coverage diverges.

{articles}

Return a JSON object with EXACTLY these keys:
{{
  "summary": "<3-5 sentence neutral briefing of the shared, verifiable facts>",
  "key_points": ["<outlet-agnostic verifiable fact>", "..."],
  "where_they_differ": [
    {{"outlet": "<outlet name>", "angle": "<what this outlet emphasizes, omits, or how it frames the story>"}}
  ]
}}"""


@dataclass
class ArticleInput:
    outlet_name: str
    lean_label: str
    body: str


@dataclass
class Briefing:
    summary: str
    key_points: list[str]
    where_they_differ: list[dict]


def _build_user_prompt(title: str, articles: list[ArticleInput]) -> str:
    blocks = []
    for a in articles[:MAX_OUTLETS]:
        body = (a.body or a.outlet_name)[:PER_OUTLET_CHARS]
        blocks.append(f"=== {a.outlet_name} ({a.lean_label}) ===\n{body}")
    return USER_TEMPLATE.format(title=title, n=len(blocks), articles="\n\n".join(blocks))


def _parse_json(text: str) -> dict:
    """Extract the first JSON object from a possibly fenced/garnished response."""
    cleaned = text.strip()
    cleaned = re.sub(r"^```(?:json)?|```$", "", cleaned, flags=re.MULTILINE).strip()
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        start, end = cleaned.find("{"), cleaned.rfind("}")
        if start != -1 and end > start:
            return json.loads(cleaned[start : end + 1])
        raise


@retry(stop=stop_after_attempt(3), wait=wait_exponential(min=2, max=20), reraise=True)
async def summarize_story(title: str, articles: list[ArticleInput]) -> Briefing:
    model = get_chat_model()
    messages = [
        ("system", SYSTEM_PROMPT),
        ("human", _build_user_prompt(title, articles)),
    ]
    resp = await model.ainvoke(messages)
    content = resp.content if isinstance(resp.content, str) else str(resp.content)
    data = _parse_json(content)

    key_points = data.get("key_points") or []
    if isinstance(key_points, str):
        key_points = [key_points]
    diffs = data.get("where_they_differ") or []
    normalized_diffs = [
        {"outlet": str(d.get("outlet", "")), "angle": str(d.get("angle", ""))}
        for d in diffs
        if isinstance(d, dict)
    ]
    return Briefing(
        summary=str(data.get("summary", "")).strip(),
        key_points=[str(p) for p in key_points][:10],
        where_they_differ=normalized_diffs[:MAX_OUTLETS],
    )


def model_name() -> str:
    return settings.chat_model
