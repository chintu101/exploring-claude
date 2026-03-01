"""
config.py
─────────
Application configuration loaded from environment variables.
All settings have sensible defaults for development.
"""

from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Central configuration object.

    Priority: env variable > .env file > default value.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # ── Application ───────────────────────────────────────────
    app_name: str = "MoodLens"
    app_version: str = "1.0.0"
    debug: bool = False

    # ── Security ──────────────────────────────────────────────
    secret_key: str = "CHANGE_ME_IN_PRODUCTION_USE_SECRETS_MANAGER"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24  # 24 hours

    # ── Database ──────────────────────────────────────────────
    database_url: str = "sqlite+aiosqlite:///./moodlens.db"

    # ── AI / Anthropic ────────────────────────────────────────
    anthropic_api_key: str = ""          # Set in .env
    ai_model: str = "claude-haiku-4-5-20251001"   # Fast + cheap for hackathon
    ai_max_tokens: int = 800

    # ── Cache ─────────────────────────────────────────────────
    cache_ttl_seconds: int = 300         # 5 minutes for analytics cache
    cache_max_size: int = 256

    # ── Subscription Tiers ────────────────────────────────────
    free_tier_monthly_entries: int = 10
    premium_price_usd: float = 9.99


# Singleton instance imported by other modules
settings = Settings()
