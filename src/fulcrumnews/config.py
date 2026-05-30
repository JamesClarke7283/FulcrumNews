"""Environment-driven configuration for FulcrumNews.

A single import-time ``settings`` singleton (pydantic-settings) is the source of
truth for every tunable. Embedding endpoint can be overridden independently of the
chat endpoint so a self-hoster can point embeddings at any OpenAI-compatible API.
"""

from __future__ import annotations

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # OpenRouter / chat LLM
    openrouter_api_key: str = Field(default="", alias="OPENROUTER_API_KEY")
    openrouter_base_url: str = Field(
        default="https://openrouter.ai/api/v1", alias="OPENROUTER_BASE_URL"
    )
    chat_model: str = Field(default="moonshotai/kimi-k2.6", alias="CHAT_MODEL")
    summary_temperature: float = Field(default=0.2, alias="SUMMARY_TEMPERATURE")
    summary_max_tokens: int = Field(default=3000, alias="SUMMARY_MAX_TOKENS")
    llm_timeout_s: int = Field(default=120, alias="LLM_TIMEOUT_S")
    openrouter_referer: str = Field(
        default="https://github.com/your/fulcrumnews", alias="OPENROUTER_REFERER"
    )

    # Embeddings
    embedding_model: str = Field(default="qwen/qwen3-embedding-4b", alias="EMBEDDING_MODEL")
    embedding_dim: int = Field(default=2560, alias="EMBEDDING_DIM")
    embeddings_base_url: str = Field(default="", alias="EMBEDDINGS_BASE_URL")
    embeddings_api_key: str = Field(default="", alias="EMBEDDINGS_API_KEY")

    # News sources
    guardian_api_key: str = Field(default="", alias="GUARDIAN_API_KEY")

    # Storage
    sqlite_path: str = Field(default="./data/fulcrum.db", alias="SQLITE_PATH")
    lancedb_path: str = Field(default="./data/lancedb", alias="LANCEDB_PATH")
    lancedb_table: str = Field(default="article_vectors", alias="LANCEDB_TABLE")

    # Clustering / blindspot
    # Loose cosine-distance band: candidates within this are CONSIDERED, but those
    # beyond `cluster_strict_distance` must also share title keywords to be merged.
    cluster_distance_threshold: float = Field(
        default=0.40, alias="CLUSTER_DISTANCE_THRESHOLD"
    )
    # Below this distance, embeddings are similar enough to merge with no lexical check.
    cluster_strict_distance: float = Field(default=0.25, alias="CLUSTER_STRICT_DISTANCE")
    # Min shared significant title tokens required to merge in the loose band.
    cluster_min_title_overlap: int = Field(default=2, alias="CLUSTER_MIN_TITLE_OVERLAP")
    # Default clustering/exploration window = 2 weeks; the refresh button can pick 1–4.
    cluster_window_hours: int = Field(default=336, alias="CLUSTER_WINDOW_HOURS")
    cluster_max_window_hours: int = Field(default=672, alias="CLUSTER_MAX_WINDOW_HOURS")
    blindspot_min_sources: int = Field(default=2, alias="BLINDSPOT_MIN_SOURCES")
    blindspot_min_share: float = Field(default=0.15, alias="BLINDSPOT_MIN_SHARE")

    # Scheduler / server
    # Volume controls (matter once you have many outlets). High so we grab each feed's
    # full depth each pull; the 2-week corpus then builds additively across refreshes.
    rss_max_items: int = Field(default=120, alias="RSS_MAX_ITEMS")
    # Summaries: every story with >= this many sources gets one. Default 2 = every story
    # shown in the feed. Set to 1 to also summarize single-source stories (far more calls).
    summary_min_sources: int = Field(default=2, alias="SUMMARY_MIN_SOURCES")
    # 0 = no cap (summarize all stale qualifying stories).
    max_summaries_per_run: int = Field(default=0, alias="MAX_SUMMARIES_PER_RUN")
    # Concurrent LLM summary calls (DB writes stay serialized).
    summary_concurrency: int = Field(default=6, alias="SUMMARY_CONCURRENCY")
    # Per-outlet body markdown fixup (LLM cleans extracted text → Markdown for display).
    format_enabled: bool = Field(default=True, alias="FORMAT_ENABLED")
    format_max_tokens: int = Field(default=6000, alias="FORMAT_MAX_TOKENS")
    format_concurrency: int = Field(default=6, alias="FORMAT_CONCURRENCY")
    # 0 = no cap. Only articles in multi-source (shown) stories are formatted.
    format_max_per_run: int = Field(default=150, alias="FORMAT_MAX_PER_RUN")
    refresh_interval_hours: float = Field(default=3, alias="REFRESH_INTERVAL_HOURS")
    admin_token: str = Field(default="", alias="ADMIN_TOKEN")
    host: str = Field(default="0.0.0.0", alias="HOST")
    port: int = Field(default=8000, alias="PORT")

    # Fetching
    user_agent: str = Field(
        default="FulcrumNewsBot/0.1 (+https://github.com/your/fulcrumnews)",
        alias="USER_AGENT",
    )
    fetch_timeout_s: float = Field(default=30, alias="FETCH_TIMEOUT_S")
    fetch_concurrency: int = Field(default=8, alias="FETCH_CONCURRENCY")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")

    # ── Derived helpers ──────────────────────────────────────────────────────
    def resolved_embeddings_base_url(self) -> str:
        return self.embeddings_base_url or self.openrouter_base_url

    def resolved_embeddings_api_key(self) -> str:
        return self.embeddings_api_key or self.openrouter_api_key

    @property
    def db_url(self) -> str:
        """Tortoise connection string for the SQLite file."""
        return f"sqlite://{self.sqlite_path}"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
