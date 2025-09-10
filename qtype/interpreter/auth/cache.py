"""
Authorization cache for QType interpreter.

This module provides a shared LRU cache for authorization sessions and tokens
across different authentication providers (AWS, OAuth2, API keys, etc.).
"""

from __future__ import annotations

import os
from typing import Any

from cachetools import LRUCache

# Global LRU cache for authorization sessions with configurable size
_AUTH_CACHE_MAX_SIZE = int(os.environ.get("AUTH_CACHE_MAX_SIZE", 128))
_AUTHORIZATION_CACHE: LRUCache[Any, Any] = LRUCache(
    maxsize=_AUTH_CACHE_MAX_SIZE
)


def get_cached_auth(auth_provider: Any) -> Any | None:
    """
    Get a cached authorization session for the given provider.

    Args:
        auth_provider: Authorization provider instance (must be hashable)

    Returns:
        Cached session/token or None if not found
    """
    return _AUTHORIZATION_CACHE.get(auth_provider)


def cache_auth(auth_provider: Any, session: Any) -> None:
    """
    Cache an authorization session for the given provider.

    Args:
        auth_provider: Authorization provider instance (must be hashable)
        session: Session or token to cache
    """
    _AUTHORIZATION_CACHE[auth_provider] = session


def clear_auth_cache() -> None:
    """
    Clear all cached authorization sessions.

    This can be useful for testing or when credential configurations change.
    """
    _AUTHORIZATION_CACHE.clear()


def get_cache_info() -> dict[str, Any]:
    """
    Get information about the current state of the authorization cache.

    Returns:
        Dictionary with cache statistics and configuration
    """
    return {
        "max_size": _AUTH_CACHE_MAX_SIZE,
        "current_size": len(_AUTHORIZATION_CACHE),
        "hits": getattr(_AUTHORIZATION_CACHE, "hits", 0),
        "misses": getattr(_AUTHORIZATION_CACHE, "misses", 0),
    }
