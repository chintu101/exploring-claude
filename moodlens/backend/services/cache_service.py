"""
services/cache_service.py
─────────────────────────
In-process TTL cache for expensive queries (analytics, AI insights).

Why cache?
──────────
The analytics dashboard aggregates potentially hundreds of journal
entries. Re-computing this on every page refresh wastes DB and CPU.
A 5-minute TTL cache gives a smooth UX while keeping data fresh enough.

Design
──────
• Uses ``cachetools.TTLCache`` – thread-safe, bounded LRU + TTL eviction.
• Keys are namespaced strings: ``"{namespace}:{user_id}"``.
• ``CacheService`` is a singleton imported by services that need caching.
• Provides typed ``get``, ``set``, ``invalidate``, and ``invalidate_user``
  helpers so callers never manipulate the raw cache dict.
"""

from __future__ import annotations

from typing import Any, Optional

from cachetools import TTLCache

from moodlens.backend.config import settings


class CacheService:
    """
    Thin wrapper around a ``TTLCache`` instance.

    Attributes
    ──────────
    _cache : The underlying TTLCache (maxsize + ttl from settings)
    """

    def __init__(self) -> None:
        self._cache: TTLCache = TTLCache(
            maxsize=settings.cache_max_size,
            ttl=settings.cache_ttl_seconds,
        )

    # ── Key helpers ────────────────────────────────────────────────────────

    @staticmethod
    def _key(namespace: str, user_id: int) -> str:
        """Build a namespaced cache key."""
        return f"{namespace}:{user_id}"

    # ── Public API ─────────────────────────────────────────────────────────

    def get(self, namespace: str, user_id: int) -> Optional[Any]:
        """
        Return the cached value for *namespace*:*user_id*, or ``None``.

        Parameters
        ──────────
        namespace : Logical group, e.g. ``"analytics"`` or ``"weekly_insight"``
        user_id   : The authenticated user's PK
        """
        return self._cache.get(self._key(namespace, user_id))

    def set(self, namespace: str, user_id: int, value: Any) -> None:
        """
        Store *value* under *namespace*:*user_id*.

        The entry will expire automatically after ``settings.cache_ttl_seconds``.
        """
        self._cache[self._key(namespace, user_id)] = value

    def invalidate(self, namespace: str, user_id: int) -> None:
        """Delete a specific cached entry (no-op if absent)."""
        self._cache.pop(self._key(namespace, user_id), None)

    def invalidate_user(self, user_id: int) -> None:
        """
        Delete ALL cache entries belonging to *user_id*.

        Called after a new journal entry is submitted so the dashboard
        reflects the latest data on the next request.
        """
        keys_to_delete = [k for k in self._cache if k.endswith(f":{user_id}")]
        for key in keys_to_delete:
            self._cache.pop(key, None)

    def clear(self) -> None:
        """Flush the entire cache (useful in tests)."""
        self._cache.clear()


# Singleton – import this instance everywhere
cache = CacheService()
