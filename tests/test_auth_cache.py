"""Unit tests for the authorization cache module.

These tests verify the basic caching functionality including storing,
retrieving, clearing, and configuration of the authorization cache.
"""

from __future__ import annotations

import os
from unittest.mock import patch

from pydantic import BaseModel

from qtype.interpreter.auth.cache import (
    cache_auth,
    clear_auth_cache,
    get_cache_info,
    get_cached_auth,
)


class MockAuthProvider(BaseModel):
    """Mock authentication provider for testing."""

    id: str
    type: str
    region: str | None = None

    class Config:
        """Pydantic configuration to make the model hashable."""

        frozen = True


class TestAuthorizationCache:
    """Test cases for the authorization cache."""

    def setup_method(self):
        """Clear cache before each test."""
        clear_auth_cache()

    def test_cache_and_retrieve_auth(self):
        """Test basic cache storage and retrieval."""
        provider = MockAuthProvider(id="test", type="mock")
        session = "mock_session_data"

        # Cache the session
        cache_auth(provider, session)

        # Retrieve the session
        cached_session = get_cached_auth(provider)

        assert cached_session == session

    def test_cache_miss_returns_none(self):
        """Test that cache miss returns None."""
        provider = MockAuthProvider(id="nonexistent", type="mock")

        cached_session = get_cached_auth(provider)

        assert cached_session is None

    def test_different_providers_different_cache_entries(self):
        """Test that different providers get different cache entries."""
        provider1 = MockAuthProvider(id="test1", type="mock")
        provider2 = MockAuthProvider(id="test2", type="mock")
        session1 = "session_1"
        session2 = "session_2"

        # Cache different sessions for different providers
        cache_auth(provider1, session1)
        cache_auth(provider2, session2)

        # Verify each provider gets its own session
        assert get_cached_auth(provider1) == session1
        assert get_cached_auth(provider2) == session2

    def test_same_provider_overwrites_cache(self):
        """Test that caching the same provider overwrites the previous entry."""
        provider = MockAuthProvider(id="test", type="mock")
        old_session = "old_session"
        new_session = "new_session"

        # Cache initial session
        cache_auth(provider, old_session)
        assert get_cached_auth(provider) == old_session

        # Cache new session for same provider
        cache_auth(provider, new_session)
        assert get_cached_auth(provider) == new_session

    def test_clear_auth_cache(self):
        """Test that clear_auth_cache removes all cached entries."""
        provider1 = MockAuthProvider(id="test1", type="mock")
        provider2 = MockAuthProvider(id="test2", type="mock")

        # Cache sessions for both providers
        cache_auth(provider1, "session1")
        cache_auth(provider2, "session2")

        # Verify they're cached
        assert get_cached_auth(provider1) is not None
        assert get_cached_auth(provider2) is not None

        # Clear cache
        clear_auth_cache()

        # Verify they're gone
        assert get_cached_auth(provider1) is None
        assert get_cached_auth(provider2) is None

    def test_get_cache_info_default_size(self):
        """Test cache info with default configuration."""
        info = get_cache_info()

        assert info["max_size"] == 128  # Default size
        assert info["current_size"] == 0  # Empty cache
        assert "hits" in info
        assert "misses" in info

    @patch.dict(os.environ, {"AUTH_CACHE_MAX_SIZE": "64"}, clear=False)
    def test_custom_cache_size_from_environment(self):
        """Test that cache size can be configured via environment variable."""
        # We need to reimport the module for the environment variable to take effect
        import importlib

        from qtype.interpreter.auth import cache

        importlib.reload(cache)

        info = cache.get_cache_info()
        assert info["max_size"] == 64

    def test_cache_info_reflects_current_size(self):
        """Test that cache info shows current number of cached items."""
        provider1 = MockAuthProvider(id="test1", type="mock")
        provider2 = MockAuthProvider(id="test2", type="mock")

        # Initially empty
        info = get_cache_info()
        assert info["current_size"] == 0

        # Add one item
        cache_auth(provider1, "session1")
        info = get_cache_info()
        assert info["current_size"] == 1

        # Add another item
        cache_auth(provider2, "session2")
        info = get_cache_info()
        assert info["current_size"] == 2

        # Clear cache
        clear_auth_cache()
        info = get_cache_info()
        assert info["current_size"] == 0

    def test_identical_providers_same_cache_key(self):
        """Test that identical provider instances use the same cache key."""
        provider1 = MockAuthProvider(
            id="test", type="mock", region="us-east-1"
        )
        provider2 = MockAuthProvider(
            id="test", type="mock", region="us-east-1"
        )

        # Cache with first provider instance
        cache_auth(provider1, "session_data")

        # Retrieve with second identical provider instance
        cached_session = get_cached_auth(provider2)

        assert cached_session == "session_data"

    def test_different_provider_fields_different_cache_keys(self):
        """Test that providers with different field values get different cache keys."""
        provider1 = MockAuthProvider(
            id="test", type="mock", region="us-east-1"
        )
        provider2 = MockAuthProvider(
            id="test", type="mock", region="us-west-2"
        )

        # Cache different sessions
        cache_auth(provider1, "east_session")
        cache_auth(provider2, "west_session")

        # Verify they're stored separately
        assert get_cached_auth(provider1) == "east_session"
        assert get_cached_auth(provider2) == "west_session"
