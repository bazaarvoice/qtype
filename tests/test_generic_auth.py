"""
Unit tests for the generic authorization context manager.
"""

from unittest.mock import MagicMock, patch

import pytest

from qtype.interpreter.auth import UnsupportedAuthProviderError, auth
from qtype.semantic.model import (
    APIKeyAuthProvider,
    AWSAuthProvider,
    OAuth2AuthProvider,
)


class TestGenericAuthContextManager:
    """Test the generic auth context manager."""

    def test_api_key_provider_returns_self(self):
        """Test that APIKeyAuthProvider returns itself."""
        provider = APIKeyAuthProvider(
            id="test-api",
            type="api_key",
            api_key="sk-test123",
            host="api.openai.com",
        )

        with auth(provider) as result:
            assert result is provider
            assert isinstance(result, APIKeyAuthProvider)
            assert result.api_key == "sk-test123"
            assert result.host == "api.openai.com"

    @patch("qtype.interpreter.auth.aws")
    def test_aws_provider_delegates_to_aws_context_manager(self, mock_aws):
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

        with auth(provider) as session:
            assert session is mock_session

        # Verify AWS context manager was called with the provider
        mock_aws.assert_called_once_with(provider)

    def test_oauth2_provider_raises_not_implemented(self):
        """Test that OAuth2AuthProvider raises NotImplementedError."""
        provider = OAuth2AuthProvider(
            id="test-oauth",
            type="oauth2",
            client_id="client123",
            client_secret="secret456",
            token_url="https://auth.example.com/token",
            scopes=[],
        )

        with pytest.raises(NotImplementedError) as exc_info:
            with auth(provider):
                pass

        assert "OAuth2 authentication is not yet implemented" in str(
            exc_info.value
        )
        assert "test-oauth" in str(exc_info.value)

    def test_unsupported_provider_raises_error(self):
        """Test that unsupported provider types raise UnsupportedAuthProviderError."""
        # Create a mock provider that doesn't match any known types
        mock_provider = MagicMock()
        mock_provider.id = "test-unknown"
        type(mock_provider).__name__ = "UnknownProvider"

        with pytest.raises(UnsupportedAuthProviderError) as exc_info:
            with auth(mock_provider):
                pass

        assert (
            "Unsupported authorization provider type: UnknownProvider"
            in str(exc_info.value)
        )
        assert "test-unknown" in str(exc_info.value)
