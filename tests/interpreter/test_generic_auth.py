"""
Unit tests for the generic authorization context manager.
"""

from unittest.mock import MagicMock, patch

import pytest

from qtype.interpreter.auth.generic import UnsupportedAuthProviderError, auth
from qtype.semantic.model import (
    APIKeyAuthProvider,
    AWSAuthProvider,
    OAuth2AuthProvider,
)


class TestGenericAuthContextManager:
    """Test the generic auth context manager."""

    def test_api_key_provider_returns_self(self, secret_manager):
        """
        Test that APIKeyAuthProvider returns a copy with resolved secrets.

        Note: The returned object is a copy (created via model_copy) to ensure
        that SecretReferences are resolved, even when the original value is
        already a plain string.
        """
        provider = APIKeyAuthProvider(
            id="test-api",
            type="api_key",
            api_key="sk-test123",
            host="api.openai.com",
        )

        with auth(provider, secret_manager) as result:
            # Result should be a copy, not the same object
            assert result is not provider
            assert isinstance(result, APIKeyAuthProvider)
            # But the values should be identical
            assert result.api_key == "sk-test123"
            assert result.host == "api.openai.com"
            assert result.id == provider.id

    @patch("qtype.interpreter.auth.generic.aws")
    def test_aws_provider_delegates_to_aws_context_manager(
        self, mock_aws, secret_manager
    ):
        """Test that AWSAuthProvider delegates to the AWS context manager."""
        provider = AWSAuthProvider(
            id="test-aws",
            type="aws",
            access_key_id=None,
            secret_access_key=None,
            session_token=None,
            profile_name="default",
            role_arn=None,
            role_session_name=None,
            external_id=None,
            region="us-east-1",
        )

        mock_session = MagicMock()
        mock_aws.return_value.__enter__.return_value = mock_session

        with auth(provider, secret_manager) as session:
            assert session is mock_session

        # Verify AWS context manager was called with the provider and secret_manager
        mock_aws.assert_called_once_with(provider, secret_manager)

    def test_oauth2_provider_returns_copy_with_resolved_secret(
        self, secret_manager
    ):
        """
        Test that OAuth2AuthProvider returns a copy with resolved secrets.

        Note: The returned object is a copy (created via model_copy) to ensure
        that SecretReferences are resolved, even when the original value is
        already a plain string.
        """
        provider = OAuth2AuthProvider(
            id="test-oauth",
            type="oauth2",
            client_id="client123",
            client_secret="secret456",
            token_url="https://auth.example.com/token",
            scopes=[],
        )

        with auth(provider, secret_manager) as result:
            # Result should be a copy, not the same object
            assert result is not provider
            assert isinstance(result, OAuth2AuthProvider)
            # But the values should be identical
            assert result.client_id == "client123"
            assert result.client_secret == "secret456"
            assert result.token_url == "https://auth.example.com/token"
            assert result.id == provider.id

    def test_unsupported_provider_raises_error(self, secret_manager):
        """Test that unsupported provider types raise UnsupportedAuthProviderError."""
        # Create a mock provider that doesn't match any known types
        mock_provider = MagicMock()
        mock_provider.id = "test-unknown"
        type(mock_provider).__name__ = "UnknownProvider"

        with pytest.raises(UnsupportedAuthProviderError) as exc_info:
            with auth(mock_provider, secret_manager):
                pass

        assert (
            "Unsupported authorization provider type: UnknownProvider"
            in str(exc_info.value)
        )
        assert "test-unknown" in str(exc_info.value)
