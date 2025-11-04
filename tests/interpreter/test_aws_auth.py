"""
Unit tests for the AWS authentication context manager.
"""

from unittest.mock import MagicMock, patch

import pytest
from botocore.exceptions import (  # type: ignore[import-untyped]
    ClientError,
    NoCredentialsError,
)

from qtype.interpreter.auth.aws import AWSAuthenticationError, aws
from qtype.semantic.model import AWSAuthProvider


@pytest.fixture
def aws_provider():
    """Create a basic AWS provider for testing."""
    return AWSAuthProvider(
        id="test-provider",
        type="aws",
        access_key_id=None,
        secret_access_key=None,
        session_token=None,
        profile_name=None,
        role_arn=None,
        role_session_name=None,
        external_id=None,
        region="us-east-1",
    )


@pytest.fixture
def profile_provider():
    """Create an AWS provider with profile configuration."""
    return AWSAuthProvider(
        id="test-provider",
        type="aws",
        access_key_id=None,
        secret_access_key=None,
        session_token=None,
        profile_name="test-profile",
        role_arn=None,
        role_session_name=None,
        external_id=None,
        region="us-west-2",
    )


@pytest.fixture
def credentials_provider():
    """Create an AWS provider with explicit credentials."""
    return AWSAuthProvider(
        id="test-provider",
        type="aws",
        access_key_id="AKIATEST",
        secret_access_key="secret",
        session_token=None,
        profile_name=None,
        role_arn=None,
        role_session_name=None,
        external_id=None,
        region="eu-west-1",
    )


@pytest.fixture
def role_provider():
    """Create an AWS provider with role assumption configuration."""
    return AWSAuthProvider(
        id="test-provider",
        type="aws",
        access_key_id=None,
        secret_access_key=None,
        session_token=None,
        profile_name="base-profile",
        role_arn="arn:aws:iam::123456789012:role/TestRole",
        role_session_name="test-session",
        external_id=None,
        region="us-east-1",
    )


class TestAWSContextManager:
    """Test the AWS authentication context manager."""

    @patch("qtype.interpreter.auth.aws.get_cached_auth")
    @patch("qtype.interpreter.auth.aws.cache_auth")
    @patch("qtype.interpreter.auth.aws._create_session")
    @patch("qtype.interpreter.auth.aws._is_session_valid")
    def test_cache_hit_with_valid_session(
        self,
        mock_is_valid,
        mock_create,
        mock_cache,
        mock_get_cached,
        aws_provider,
    ):
        """Test that cached valid sessions are returned without recreation."""
        cached_session = MagicMock()
        mock_get_cached.return_value = cached_session
        mock_is_valid.return_value = True

        with aws(aws_provider) as session:
            assert session is cached_session

        mock_get_cached.assert_called_once_with(aws_provider)
        mock_is_valid.assert_called_once_with(cached_session)
        mock_create.assert_not_called()
        mock_cache.assert_not_called()

    @patch("qtype.interpreter.auth.aws.get_cached_auth")
    @patch("qtype.interpreter.auth.aws.cache_auth")
    @patch("qtype.interpreter.auth.aws._create_session")
    @patch("qtype.interpreter.auth.aws._is_session_valid")
    def test_cache_miss_creates_new_session(
        self,
        mock_is_valid,
        mock_create,
        mock_cache,
        mock_get_cached,
        aws_provider,
    ):
        """Test that when no cached session exists, a new one is created."""
        new_session = MagicMock()
        mock_get_cached.return_value = None
        mock_create.return_value = new_session

        with aws(aws_provider) as session:
            assert session is new_session

        mock_get_cached.assert_called_once_with(aws_provider)
        mock_is_valid.assert_not_called()
        mock_create.assert_called_once_with(aws_provider, None)
        mock_cache.assert_called_once_with(aws_provider, new_session)

    @patch("qtype.interpreter.auth.aws.get_cached_auth")
    @patch("qtype.interpreter.auth.aws.cache_auth")
    @patch("qtype.interpreter.auth.aws._create_session")
    @patch("qtype.interpreter.auth.aws._is_session_valid")
    def test_invalid_cached_session_creates_new(
        self,
        mock_is_valid,
        mock_create,
        mock_cache,
        mock_get_cached,
        aws_provider,
    ):
        """Test that invalid cached sessions are replaced with new ones."""
        cached_session = MagicMock()
        new_session = MagicMock()
        mock_get_cached.return_value = cached_session
        mock_is_valid.return_value = False
        mock_create.return_value = new_session

        with aws(aws_provider) as session:
            assert session is new_session

        mock_get_cached.assert_called_once_with(aws_provider)
        mock_is_valid.assert_called_once_with(cached_session)
        mock_create.assert_called_once_with(aws_provider, None)
        mock_cache.assert_called_once_with(aws_provider, new_session)

    @patch("qtype.interpreter.auth.aws._create_session")
    def test_session_without_credentials_raises_error(
        self, mock_create, aws_provider
    ):
        """Test that authentication errors are properly wrapped."""
        mock_create.side_effect = AWSAuthenticationError(
            "No credentials found"
        )

        with pytest.raises(
            AWSAuthenticationError, match="No credentials found"
        ):
            with aws(aws_provider):
                pass

    @patch("qtype.interpreter.auth.aws._create_session")
    def test_client_error_raises_aws_authentication_error(
        self, mock_create, aws_provider
    ):
        """Test that boto3 ClientError is wrapped in AWSAuthenticationError."""
        client_error = ClientError(
            {"Error": {"Code": "AccessDenied", "Message": "Access denied"}},
            "GetCallerIdentity",
        )
        mock_create.side_effect = client_error

        with pytest.raises(AWSAuthenticationError):
            with aws(aws_provider):
                pass


class TestSessionValidation:
    """Test session validation functionality."""

    def test_session_valid_with_credentials(self):
        """Test that sessions with valid credentials are marked as valid."""
        from qtype.interpreter.auth.aws import _is_session_valid

        mock_session = MagicMock()
        mock_credentials = MagicMock()
        mock_credentials.token = None
        mock_session.get_credentials.return_value = mock_credentials

        assert _is_session_valid(mock_session) is True
        mock_session.get_credentials.assert_called_once()

    def test_session_invalid_without_credentials(self):
        """Test that sessions without credentials are marked as invalid."""
        from qtype.interpreter.auth.aws import _is_session_valid

        mock_session = MagicMock()
        mock_session.get_credentials.return_value = None

        assert _is_session_valid(mock_session) is False

    def test_session_valid_with_temporary_credentials(self):
        """Test that sessions with valid temporary credentials are marked as valid."""
        from qtype.interpreter.auth.aws import _is_session_valid

        mock_session = MagicMock()
        mock_credentials = MagicMock()
        mock_credentials.token = "temp-token"
        mock_session.get_credentials.return_value = mock_credentials

        mock_sts_client = MagicMock()
        mock_session.client.return_value = mock_sts_client

        assert _is_session_valid(mock_session) is True
        mock_session.client.assert_called_once_with("sts")
        mock_sts_client.get_caller_identity.assert_called_once()

    def test_session_invalid_on_client_error(self):
        """Test that sessions causing ClientError are marked as invalid."""
        from qtype.interpreter.auth.aws import _is_session_valid

        mock_session = MagicMock()
        mock_credentials = MagicMock()
        mock_credentials.token = "temp-token"
        mock_session.get_credentials.return_value = mock_credentials

        mock_sts_client = MagicMock()
        mock_sts_client.get_caller_identity.side_effect = ClientError(
            {"Error": {"Code": "ExpiredToken"}}, "GetCallerIdentity"
        )
        mock_session.client.return_value = mock_sts_client

        assert _is_session_valid(mock_session) is False

    def test_session_invalid_on_no_credentials_error(self):
        """Test that sessions causing NoCredentialsError are marked as invalid."""
        from qtype.interpreter.auth.aws import _is_session_valid

        mock_session = MagicMock()
        mock_session.get_credentials.side_effect = NoCredentialsError()

        assert _is_session_valid(mock_session) is False


class TestCreateSession:
    """Test session creation functionality."""

    @patch("boto3.Session")
    def test_create_session_with_profile(
        self, mock_session_class, profile_provider
    ):
        """Test creating a session with an AWS profile."""
        from qtype.interpreter.auth.aws import _create_session

        mock_session = MagicMock()
        mock_session_class.return_value = mock_session

        result = _create_session(profile_provider)

        mock_session_class.assert_called_once_with(
            profile_name="test-profile", region_name="us-west-2"
        )
        assert result is mock_session

    @patch("boto3.Session")
    def test_create_session_with_credentials(
        self, mock_session_class, credentials_provider
    ):
        """Test creating a session with explicit credentials."""
        from qtype.interpreter.auth.aws import _create_session

        mock_session = MagicMock()
        mock_session_class.return_value = mock_session

        result = _create_session(credentials_provider)

        mock_session_class.assert_called_once_with(
            aws_access_key_id="AKIATEST",
            aws_secret_access_key="secret",
            region_name="eu-west-1",
        )
        assert result is mock_session

    @patch("qtype.interpreter.auth.aws._assume_role_session")
    @patch("boto3.Session")
    def test_create_session_with_role_assumption(
        self, mock_session_class, mock_assume_role, role_provider
    ):
        """Test creating a session that assumes a role."""
        from qtype.interpreter.auth.aws import _create_session

        base_session = MagicMock()
        role_session = MagicMock()
        mock_session_class.return_value = base_session
        mock_assume_role.return_value = role_session

        result = _create_session(role_provider)

        mock_assume_role.assert_called_once_with(base_session, role_provider)
        assert result is role_session


class TestAssumeRoleSession:
    """Test role assumption functionality."""

    def test_assume_role_without_arn_raises_error(self, aws_provider):
        """Test that attempting to assume role without ARN raises an error."""
        from qtype.interpreter.auth.aws import _assume_role_session

        base_session = MagicMock()

        with pytest.raises(
            AWSAuthenticationError,
            match="role_arn is required for role assumption",
        ):
            _assume_role_session(base_session, aws_provider)

    @patch("boto3.Session")
    def test_assume_role_success(self, mock_session_class, role_provider):
        """Test successful role assumption."""
        from qtype.interpreter.auth.aws import _assume_role_session

        base_session = MagicMock()
        base_session.region_name = "us-east-1"

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

        # Update role_provider to have the right region for assertion
        role_provider = AWSAuthProvider(
            id="test-provider",
            type="aws",
            access_key_id=None,
            secret_access_key=None,
            session_token=None,
            profile_name="base-profile",
            role_arn="arn:aws:iam::123456789012:role/TestRole",
            role_session_name="test-session",
            external_id=None,
            region="us-west-2",
        )

        result = _assume_role_session(base_session, role_provider)

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

    def test_assume_role_client_error_wrapped(self, role_provider):
        """Test that ClientError during role assumption is properly wrapped."""
        from qtype.interpreter.auth.aws import _assume_role_session

        base_session = MagicMock()
        mock_sts_client = MagicMock()
        mock_sts_client.assume_role.side_effect = ClientError(
            {"Error": {"Code": "AccessDenied", "Message": "Access denied"}},
            "AssumeRole",
        )
        base_session.client.return_value = mock_sts_client

        with pytest.raises(
            AWSAuthenticationError, match="Failed to assume role"
        ):
            _assume_role_session(base_session, role_provider)
