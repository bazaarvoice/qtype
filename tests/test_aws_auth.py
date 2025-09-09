"""
Unit tests for the AWS authentication context manager.
"""

# Get the actual module to avoid namespace conflicts from __init__.py re-exports
import sys
from unittest.mock import MagicMock, patch

import pytest
from botocore.exceptions import ClientError, NoCredentialsError

from qtype.interpreter.auth.aws import AWSAuthenticationError, aws
from qtype.semantic.model import AWSAuthProvider

sys.modules[
    "qtype.interpreter.auth.aws"
]  # This forces the module to be loaded
# Now we can patch the module-level functions directly


def create_aws_provider(**kwargs):
    """Helper to create AWSAuthProvider with required fields."""
    defaults = {
        "id": "test-provider",
        "type": "aws",
        "access_key_id": None,
        "secret_access_key": None,
        "session_token": None,
        "profile_name": None,
        "role_arn": None,
        "role_session_name": None,
        "external_id": None,
        "region": None,
    }
    defaults.update(kwargs)
    return AWSAuthProvider(**defaults)


class TestAWSContextManager:
    """Test the AWS authentication context manager."""

    def test_cache_hit_with_valid_session(self):
        """Test that cached valid sessions are returned without recreation."""
        # Setup
        provider = create_aws_provider(region="us-east-1")
        cached_session = MagicMock()

        with (
            patch(
                "qtype.interpreter.auth.aws.get_cached_auth"
            ) as mock_get_cached,
            patch("qtype.interpreter.auth.aws.cache_auth") as mock_cache,
            patch("qtype.interpreter.auth.aws._create_session") as mock_create,
            patch(
                "qtype.interpreter.auth.aws._is_session_valid"
            ) as mock_is_valid,
        ):
            mock_get_cached.return_value = cached_session
            mock_is_valid.return_value = True

            # Execute
            with aws(provider) as session:
                result_session = session

            # Verify
            mock_get_cached.assert_called_once_with(provider)
            mock_is_valid.assert_called_once_with(cached_session)
            mock_create.assert_not_called()
            mock_cache.assert_not_called()
            assert result_session is cached_session

    def test_cache_miss_creates_new_session(self):
        """Test that when no cached session exists, a new one is created."""
        # Setup
        provider = create_aws_provider(region="us-east-1")
        new_session = MagicMock()

        with (
            patch(
                "qtype.interpreter.auth.aws.get_cached_auth"
            ) as mock_get_cached,
            patch("qtype.interpreter.auth.aws.cache_auth") as mock_cache,
            patch("qtype.interpreter.auth.aws._create_session") as mock_create,
            patch(
                "qtype.interpreter.auth.aws._is_session_valid"
            ) as mock_is_valid,
        ):
            mock_get_cached.return_value = None
            mock_create.return_value = new_session

            # Execute
            with aws(provider) as session:
                result_session = session

            # Verify
            mock_get_cached.assert_called_once_with(provider)
            mock_is_valid.assert_not_called()
            mock_create.assert_called_once_with(provider)
            mock_cache.assert_called_once_with(provider, new_session)
            assert result_session is new_session

    def test_invalid_cached_session_creates_new(self):
        """Test that invalid cached sessions are replaced with new ones."""
        # Setup
        provider = create_aws_provider(region="us-east-1")
        cached_session = MagicMock()
        new_session = MagicMock()

        with (
            patch(
                "qtype.interpreter.auth.aws.get_cached_auth"
            ) as mock_get_cached,
            patch("qtype.interpreter.auth.aws.cache_auth") as mock_cache,
            patch("qtype.interpreter.auth.aws._create_session") as mock_create,
            patch(
                "qtype.interpreter.auth.aws._is_session_valid"
            ) as mock_is_valid,
        ):
            mock_get_cached.return_value = cached_session
            mock_is_valid.return_value = False
            mock_create.return_value = new_session

            # Execute
            with aws(provider) as session:
                result_session = session

            # Verify
            mock_get_cached.assert_called_once_with(provider)
            mock_is_valid.assert_called_once_with(cached_session)
            mock_create.assert_called_once_with(provider)
            mock_cache.assert_called_once_with(provider, new_session)
            assert result_session is new_session

    def test_session_without_credentials_raises_error(self):
        """Test that authentication errors are properly wrapped."""
        # Setup
        provider = create_aws_provider(region="us-east-1")

        with patch(
            "qtype.interpreter.auth.aws._create_session"
        ) as mock_create:
            mock_create.side_effect = AWSAuthenticationError(
                "No credentials found"
            )

            # Execute & Verify
            with pytest.raises(
                AWSAuthenticationError, match="No credentials found"
            ):
                with aws(provider):
                    pass

    def test_client_error_raises_aws_authentication_error(self):
        """Test that boto3 ClientError is wrapped in AWSAuthenticationError."""
        # Setup
        provider = create_aws_provider(region="us-east-1")
        client_error = ClientError(
            {"Error": {"Code": "AccessDenied", "Message": "Access denied"}},
            "GetCallerIdentity",
        )

        with patch(
            "qtype.interpreter.auth.aws._create_session"
        ) as mock_create:
            mock_create.side_effect = client_error

            # Execute & Verify
            with pytest.raises(AWSAuthenticationError):
                with aws(provider):
                    pass


class TestSessionValidation:
    """Test session validation functionality."""

    @patch("boto3.Session")
    def test_session_valid_with_credentials(self, mock_session_class):
        """Test that sessions with valid credentials are marked as valid."""
        from qtype.interpreter.auth.aws import _is_session_valid

        # Setup
        mock_session = MagicMock()
        mock_credentials = MagicMock()
        mock_credentials.token = None
        mock_session.get_credentials.return_value = mock_credentials

        # Execute
        result = _is_session_valid(mock_session)

        # Verify
        assert result is True
        mock_session.get_credentials.assert_called_once()

    @patch("boto3.Session")
    def test_session_invalid_without_credentials(self, mock_session_class):
        """Test that sessions without credentials are marked as invalid."""
        from qtype.interpreter.auth.aws import _is_session_valid

        # Setup
        mock_session = MagicMock()
        mock_session.get_credentials.return_value = None

        # Execute
        result = _is_session_valid(mock_session)

        # Verify
        assert result is False

    @patch("boto3.Session")
    def test_session_valid_with_temporary_credentials(
        self, mock_session_class
    ):
        """Test that sessions with valid temporary credentials are marked as valid."""
        from qtype.interpreter.auth.aws import _is_session_valid

        # Setup
        mock_session = MagicMock()
        mock_credentials = MagicMock()
        mock_credentials.token = "temp-token"
        mock_session.get_credentials.return_value = mock_credentials

        mock_sts_client = MagicMock()
        mock_session.client.return_value = mock_sts_client

        # Execute
        result = _is_session_valid(mock_session)

        # Verify
        assert result is True
        mock_session.client.assert_called_once_with("sts")
        mock_sts_client.get_caller_identity.assert_called_once()

    @patch("boto3.Session")
    def test_session_invalid_on_client_error(self, mock_session_class):
        """Test that sessions causing ClientError are marked as invalid."""
        from qtype.interpreter.auth.aws import _is_session_valid

        # Setup
        mock_session = MagicMock()
        mock_credentials = MagicMock()
        mock_credentials.token = "temp-token"
        mock_session.get_credentials.return_value = mock_credentials

        mock_sts_client = MagicMock()
        mock_sts_client.get_caller_identity.side_effect = ClientError(
            {"Error": {"Code": "ExpiredToken"}}, "GetCallerIdentity"
        )
        mock_session.client.return_value = mock_sts_client

        # Execute
        result = _is_session_valid(mock_session)

        # Verify
        assert result is False

    @patch("boto3.Session")
    def test_session_invalid_on_no_credentials_error(self, mock_session_class):
        """Test that sessions causing NoCredentialsError are marked as invalid."""
        from qtype.interpreter.auth.aws import _is_session_valid

        # Setup
        mock_session = MagicMock()
        mock_session.get_credentials.side_effect = NoCredentialsError()

        # Execute
        result = _is_session_valid(mock_session)

        # Verify
        assert result is False


class TestCreateSession:
    """Test session creation functionality."""

    @patch("boto3.Session")
    def test_create_session_with_profile(self, mock_session_class):
        """Test creating a session with an AWS profile."""
        from qtype.interpreter.auth.aws import _create_session

        # Setup
        provider = create_aws_provider(
            profile_name="test-profile", region="us-west-2"
        )
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session

        # Execute
        result = _create_session(provider)

        # Verify
        mock_session_class.assert_called_once_with(
            profile_name="test-profile", region_name="us-west-2"
        )
        assert result is mock_session

    @patch("boto3.Session")
    def test_create_session_with_credentials(self, mock_session_class):
        """Test creating a session with explicit credentials."""
        from qtype.interpreter.auth.aws import _create_session

        # Setup
        provider = create_aws_provider(
            access_key_id="AKIATEST",
            secret_access_key="secret",
            region="eu-west-1",
        )
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session

        # Execute
        result = _create_session(provider)

        # Verify
        mock_session_class.assert_called_once_with(
            aws_access_key_id="AKIATEST",
            aws_secret_access_key="secret",
            region_name="eu-west-1",
        )
        assert result is mock_session

    def test_create_session_with_role_assumption(self):
        """Test creating a session that assumes a role."""
        from qtype.interpreter.auth.aws import _create_session

        # Setup
        provider = create_aws_provider(
            profile_name="base-profile",
            role_arn="arn:aws:iam::123456789012:role/TestRole",
            region="us-east-1",
        )
        base_session = MagicMock()
        role_session = MagicMock()

        with (
            patch("boto3.Session", return_value=base_session),
            patch(
                "qtype.interpreter.auth.aws._assume_role_session",
                return_value=role_session,
            ) as mock_assume_role,
        ):
            # Execute
            result = _create_session(provider)

            # Verify
            mock_assume_role.assert_called_once_with(base_session, provider)
            assert result is role_session


class TestAssumeRoleSession:
    """Test role assumption functionality."""

    def test_assume_role_without_arn_raises_error(self):
        """Test that attempting to assume role without ARN raises an error."""
        from qtype.interpreter.auth.aws import _assume_role_session

        # Setup
        base_session = MagicMock()
        provider = create_aws_provider(region="us-east-1")  # No role_arn

        # Execute & Verify
        with pytest.raises(
            AWSAuthenticationError,
            match="role_arn is required for role assumption",
        ):
            _assume_role_session(base_session, provider)

    @patch("boto3.Session")
    def test_assume_role_success(self, mock_session_class):
        """Test successful role assumption."""
        from qtype.interpreter.auth.aws import _assume_role_session

        # Setup
        base_session = MagicMock()
        base_session.region_name = "us-east-1"
        provider = create_aws_provider(
            role_arn="arn:aws:iam::123456789012:role/TestRole",
            role_session_name="test-session",
            region="us-west-2",
        )

        mock_sts_client = MagicMock()
        mock_sts_client.assume_role.return_value = {
            "Credentials": {
                "AccessKeyId": "ASIATEST",
                "SecretAccessKey": "temp-secret",
                "SessionToken": "temp-token",
            }
        }
        base_session.client.return_value = mock_sts_client

        mock_role_session = MagicMock()
        mock_session_class.return_value = mock_role_session

        # Execute
        result = _assume_role_session(base_session, provider)

        # Verify
        base_session.client.assert_called_once_with("sts")
        mock_sts_client.assume_role.assert_called_once_with(
            RoleArn="arn:aws:iam::123456789012:role/TestRole",
            RoleSessionName="test-session",
        )
        mock_session_class.assert_called_once_with(
            aws_access_key_id="ASIATEST",
            aws_secret_access_key="temp-secret",
            aws_session_token="temp-token",
            region_name="us-west-2",
        )
        assert result is mock_role_session

    def test_assume_role_client_error_wrapped(self):
        """Test that ClientError during role assumption is properly wrapped."""
        from qtype.interpreter.auth.aws import _assume_role_session

        # Setup
        base_session = MagicMock()
        provider = create_aws_provider(
            role_arn="arn:aws:iam::123456789012:role/TestRole",
            role_session_name="test-session",
            region="us-east-1",
        )

        mock_sts_client = MagicMock()
        mock_sts_client.assume_role.side_effect = ClientError(
            {"Error": {"Code": "AccessDenied", "Message": "Access denied"}},
            "AssumeRole",
        )
        base_session.client.return_value = mock_sts_client

        # Execute & Verify
        with pytest.raises(
            AWSAuthenticationError, match="Failed to assume role"
        ):
            _assume_role_session(base_session, provider)
