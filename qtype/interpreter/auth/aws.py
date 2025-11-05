"""
AWS authentication context manager for QType interpreter.

This module provides a context manager for creating boto3 sessions using
AWSAuthProvider configuration from the semantic model.
"""

from __future__ import annotations

from contextlib import contextmanager
from typing import Any, Generator

import boto3  # type: ignore[import-untyped]
from botocore.exceptions import (  # type: ignore[import-untyped]
    ClientError,
    NoCredentialsError,
)

from qtype.interpreter.auth.cache import cache_auth, get_cached_auth
from qtype.interpreter.base.secrets import SecretManagerBase
from qtype.semantic.model import AWSAuthProvider


class AWSAuthenticationError(Exception):
    """Raised when AWS authentication fails."""

    pass


def _is_session_valid(session: boto3.Session) -> bool:
    """
    Check if a boto3 session is still valid by testing credential access.

    Args:
        session: The boto3 session to validate

    Returns:
        bool: True if the session is valid, False otherwise
    """
    try:
        credentials = session.get_credentials()
        if credentials is None:
            return False

        # For temporary credentials, check if they're still valid
        if hasattr(credentials, "token") and credentials.token:
            # Create a test STS client to verify the credentials
            sts_client = session.client("sts")
            sts_client.get_caller_identity()

        return True
    except (ClientError, NoCredentialsError):
        return False
    except Exception:
        # Any other exception means the session is likely invalid
        return False


@contextmanager
def aws(
    aws_provider: AWSAuthProvider,
    secret_manager: SecretManagerBase,
) -> Generator[boto3.Session, None, None]:
    """
    Create a boto3 Session using AWS authentication provider configuration.

    This context manager creates a boto3 Session based on the authentication
    method specified in the AWSAuthProvider. Sessions are cached using an LRU
    cache to avoid recreating them unnecessarily. The cache size can be configured
    via the AUTH_CACHE_MAX_SIZE environment variable (default: 128).

    It supports:
    - Direct credentials (access key + secret key + optional session token)
    - AWS profiles from shared credentials/config files
    - Role assumption (with optional external ID and MFA)
    - Environment-based authentication (when no explicit credentials provided)

    Caching behavior:
    - Sessions are cached based on the AWSAuthProvider configuration
    - Cached sessions are validated before reuse to check for expiration
    - Invalid or expired sessions are evicted and recreated

    Args:
        aws_provider: AWSAuthProvider instance containing authentication configuration

    Yields:
        boto3.Session: Configured boto3 session ready for creating AWS service clients

    Raises:
        AWSAuthenticationError: When authentication fails or configuration is invalid

    Example:
        ```python
        from qtype.semantic.model import AWSAuthProvider
        from qtype.interpreter.auth.aws import aws

        aws_auth = AWSAuthProvider(
            id="my-aws-auth",
            type="aws",
            access_key_id="AKIA...",
            secret_access_key="...",
            region="us-east-1"
        )

        with aws(aws_auth) as session:
            athena_client = session.client("athena")
            s3_client = session.client("s3")
        ```
    """
    try:
        # Check cache first - use provider object directly as cache key
        cached_session = get_cached_auth(aws_provider)

        if cached_session is not None and _is_session_valid(cached_session):
            # Cache hit with valid session
            yield cached_session
            return

        # Cache miss or invalid session - create new session
        session = _create_session(aws_provider, secret_manager)

        # Validate the session by attempting to get credentials
        credentials = session.get_credentials()
        if credentials is None:
            raise AWSAuthenticationError(
                f"Failed to obtain AWS credentials for provider '{aws_provider.id}'"
            )

        # Cache the valid session using provider object as key
        cache_auth(aws_provider, session)

        yield session

    except (ClientError, NoCredentialsError) as e:
        raise AWSAuthenticationError(
            f"AWS authentication failed for provider '{aws_provider.id}': {e}"
        ) from e
    except Exception as e:
        raise AWSAuthenticationError(
            f"Unexpected error during AWS authentication for provider '{aws_provider.id}': {e}"
        ) from e


def _create_session(
    aws_provider: AWSAuthProvider,
    secret_manager: SecretManagerBase,
) -> boto3.Session:
    """
    Create a boto3 Session based on the AWS provider configuration.

    Args:
        aws_provider: AWSAuthProvider with authentication details
        secret_manager: Secret manager for resolving SecretReferences

    Returns:
        boto3.Session: Configured session

    Raises:
        AWSAuthenticationError: If configuration is invalid
    """
    session_kwargs: dict[str, Any] = {}

    # Add region if specified
    if aws_provider.region:
        session_kwargs["region_name"] = aws_provider.region

    # Handle different authentication methods
    if aws_provider.profile_name:
        # Use AWS profile from shared credentials/config files
        session_kwargs["profile_name"] = aws_provider.profile_name

    elif aws_provider.access_key_id and aws_provider.secret_access_key:
        # Use direct credentials - resolve secrets
        context = f"AWS auth provider '{aws_provider.id}'"
        access_key = secret_manager(aws_provider.access_key_id, context)
        secret_key = secret_manager(aws_provider.secret_access_key, context)
        session_kwargs["aws_access_key_id"] = access_key
        session_kwargs["aws_secret_access_key"] = secret_key

        if aws_provider.session_token:
            session_token = secret_manager(aws_provider.session_token, context)
            session_kwargs["aws_session_token"] = session_token

    # Create the base session
    session = boto3.Session(**session_kwargs)

    # Handle role assumption if specified
    if aws_provider.role_arn:
        session = _assume_role_session(session, aws_provider)

    return session


def _assume_role_session(
    base_session: boto3.Session, aws_provider: AWSAuthProvider
) -> boto3.Session:
    """
    Create a new session by assuming an IAM role.

    Args:
        base_session: The base session to use for assuming the role
        aws_provider: AWSAuthProvider with role configuration

    Returns:
        boto3.Session: New session with assumed role credentials

    Raises:
        AWSAuthenticationError: If role assumption fails
    """
    if not aws_provider.role_arn:
        raise AWSAuthenticationError(
            "role_arn is required for role assumption"
        )

    try:
        sts_client = base_session.client("sts")

        # Prepare AssumeRole parameters
        assume_role_params: dict[str, Any] = {
            "RoleArn": aws_provider.role_arn,
            "RoleSessionName": aws_provider.role_session_name
            or f"qtype-session-{aws_provider.id}",
        }

        if aws_provider.external_id:
            assume_role_params["ExternalId"] = aws_provider.external_id

        # Assume the role
        response = sts_client.assume_role(**assume_role_params)
        credentials = response["Credentials"]

        # Create new session with temporary credentials
        return boto3.Session(
            aws_access_key_id=credentials["AccessKeyId"],
            aws_secret_access_key=credentials["SecretAccessKey"],
            aws_session_token=credentials["SessionToken"],
            region_name=aws_provider.region or base_session.region_name,
        )

    except ClientError as e:
        error_code = e.response.get("Error", {}).get("Code", "Unknown")
        raise AWSAuthenticationError(
            f"Failed to assume role '{aws_provider.role_arn}': {error_code} - {e}"
        ) from e
