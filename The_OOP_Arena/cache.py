"""
CodeQuest — Cache Layer
========================
Wraps cachetools.TTLCache for expensive-to-compute static data.

Cached items:
  - Class hierarchy tree (never changes; long TTL)
  - Wave enemy compositions (changes per wave; short TTL)
  - OOP concept definitions (static content)

The cache is module-level (process-scoped). On Vercel each serverless
invocation gets a cold or warm container; warm containers share the cache
across requests within the same execution context, giving meaningful speedups.
"""

from __future__ import annotations

import functools
from typing import Any

from cachetools import TTLCache

# ── Cache instances ──
# maxsize: max number of entries; ttl: seconds before expiry

# Static content that never changes (1-hour TTL, 50 entries)
_STATIC_CACHE: TTLCache = TTLCache(maxsize=50, ttl=3600)

# Wave data: changes per new game but static within a game (10-minute TTL)
_WAVE_CACHE: TTLCache = TTLCache(maxsize=20, ttl=600)


class GameCache:
    """Thin wrapper providing a consistent interface to the TTL caches.

    All methods are static so they can be called without an instance.
    """

    # ── Static cache (hierarchy, OOP concepts) ──

    @staticmethod
    def get_static(key: str) -> Any | None:
        """Retrieve a value from the static cache. Returns None on miss."""
        return _STATIC_CACHE.get(key)

    @staticmethod
    def set_static(key: str, value: Any) -> None:
        """Store a value in the static cache."""
        _STATIC_CACHE[key] = value

    # ── Wave cache (enemy composition per wave) ──

    @staticmethod
    def get_wave(wave: int) -> list[str] | None:
        """Retrieve the cached enemy list for a wave. Returns None on miss."""
        return _WAVE_CACHE.get(f"wave_{wave}")

    @staticmethod
    def set_wave(wave: int, enemy_types: list[str]) -> None:
        """Store the enemy composition for a given wave."""
        _WAVE_CACHE[f"wave_{wave}"] = enemy_types

    @staticmethod
    def clear_all() -> None:
        """Flush all caches (useful in tests)."""
        _STATIC_CACHE.clear()
        _WAVE_CACHE.clear()

    @staticmethod
    def stats() -> dict:
        """Return cache hit/miss info for debugging."""
        return {
            "static_cache_size": len(_STATIC_CACHE),
            "static_cache_maxsize": _STATIC_CACHE.maxsize,
            "wave_cache_size": len(_WAVE_CACHE),
            "wave_cache_maxsize": _WAVE_CACHE.maxsize,
        }


def cached_static(key: str):
    """Decorator: cache the return value of a zero-argument function in the static cache.

    Usage:
        @cached_static("my_key")
        def expensive_computation() -> dict:
            ...

    On first call, runs the function and stores the result.
    On subsequent calls, returns the cached value instantly.
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            cached = GameCache.get_static(key)
            if cached is not None:
                return cached
            result = func(*args, **kwargs)
            GameCache.set_static(key, result)
            return result
        return wrapper
    return decorator
