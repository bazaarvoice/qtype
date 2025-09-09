"""
AWS authentication context manager for QType interpreter.

This module provides a context manager for creating boto3 sessions using
AWSAuthProvider configuration from the semantic model.
"""

from __future__ import annotations

from contextlib import contextmanager
from typing import Any, Generator

import boto3
from botocore.exceptions import ClientError, NoCredentialsError

from qtype.semantic.model import AWSAuthProvider


class AWSAuthenticationError(Exception):
    """Raised when AWS authentication fails."""

    pass


@contextmanager
def aws(aws_provider: AWSAuthProvider) -> Generator[boto3.Session, None, None]:
    """
    Create a boto3 Session using AWS authentication provider configuration.

    This context manager creates a boto3 Session based on the authentication
    method specified in the AWSAuthProvider. It supports:
    - Direct credentials (access key + secret key + optional session token)
    - AWS profiles from shared credentials/config files
    - Role assumption (with optional external ID and MFA)
    - Environment-based authentication (when no explicit credentials provided)

    Args:
        aws_provider: AWSAuthProvider instance containing authentication configuration

    Yields:
        boto3.Session: Configured boto3 session ready for creating AWS service clients

    Raises:
        AWSAuthenticationError: When authentication fails or configuration is invalid

    Example:
        ```python
        from qtype.semantic.model import AWSAuthProvider
        from qtype.interpreter.auth import aws

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
        session = _create_session(aws_provider)

        # Validate the session by attempting to get credentials
        credentials = session.get_credentials()
        if credentials is None:
            raise AWSAuthenticationError(
                f"Failed to obtain AWS credentials for provider '{aws_provider.id}'"
            )

        yield session

    except (ClientError, NoCredentialsError) as e:
        raise AWSAuthenticationError(
            f"AWS authentication failed for provider '{aws_provider.id}': {e}"
        ) from e
    except Exception as e:
        raise AWSAuthenticationError(
            f"Unexpected error during AWS authentication for provider '{aws_provider.id}': {e}"
        ) from e


def _create_session(aws_provider: AWSAuthProvider) -> boto3.Session:
    """
    Create a boto3 Session based on the AWS provider configuration.

    Args:
        aws_provider: AWSAuthProvider with authentication details

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
        # Use direct credentials
        session_kwargs["aws_access_key_id"] = aws_provider.access_key_id
        session_kwargs["aws_secret_access_key"] = (
            aws_provider.secret_access_key
        )

        if aws_provider.session_token:
            session_kwargs["aws_session_token"] = aws_provider.session_token

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
