"""
Generic authorization context manager for QType interpreter.

This module provides a unified context manager that can handle any AuthorizationProvider
type and return the appropriate session or provider instance.
"""

from __future__ import annotations

from contextlib import contextmanager
from typing import Generator

import boto3  # type: ignore[import-untyped]

from qtype.interpreter.auth.aws import aws
from qtype.semantic.model import (
    APIKeyAuthProvider,
    AuthorizationProvider,
    AWSAuthProvider,
    OAuth2AuthProvider,
)


class UnsupportedAuthProviderError(Exception):
    """Raised when an unsupported authorization provider type is used."""

    pass


@contextmanager
def auth(
    auth_provider: AuthorizationProvider,
) -> Generator[boto3.Session | APIKeyAuthProvider, None, None]:
    """
    Create an appropriate session or provider instance based on the auth provider type.

    This context manager dispatches to the appropriate authentication handler based
    on the type of AuthorizationProvider:
    - AWSAuthProvider: Returns a configured boto3.Session
    - APIKeyAuthProvider: Returns the provider instance (contains the API key)
    - OAuth2AuthProvider: Raises NotImplementedError (not yet supported)

    Args:
        auth_provider: AuthorizationProvider instance of any supported type

    Yields:
        boto3.Session | APIKeyAuthProvider: The appropriate session or provider instance

    Raises:
        UnsupportedAuthProviderError: When an unsupported provider type is used
        NotImplementedError: When OAuth2AuthProvider is used (not yet implemented)

    Example:
        ```python
        from qtype.semantic.model import AWSAuthProvider, APIKeyAuthProvider
        from qtype.interpreter.auth.generic import auth

        # AWS provider - returns boto3.Session
        aws_auth = AWSAuthProvider(
            id="my-aws-auth",
            type="aws",
            access_key_id="AKIA...",
            secret_access_key="...",
            region="us-east-1"
        )

        with auth(aws_auth) as session:
            s3_client = session.client("s3")

        # API Key provider - returns the provider itself
        api_auth = APIKeyAuthProvider(
            id="my-api-auth",
            type="api_key",
            api_key="sk-...",
            host="api.openai.com"
        )

        with auth(api_auth) as provider:
            headers = {"Authorization": f"Bearer {provider.api_key}"}
        ```
    """
    if isinstance(auth_provider, AWSAuthProvider):
        # Use AWS-specific context manager
        with aws(auth_provider) as session:
            yield session

    elif isinstance(auth_provider, APIKeyAuthProvider):
        # For API key providers, just return the provider itself
        # The caller can access provider.api_key and provider.host
        yield auth_provider

    elif isinstance(auth_provider, OAuth2AuthProvider):
        # OAuth2 not yet implemented
        raise NotImplementedError(
            f"OAuth2 authentication is not yet implemented for provider '{auth_provider.id}'"
        )

    else:
        # Unknown provider type
        raise UnsupportedAuthProviderError(
            f"Unsupported authorization provider type: {type(auth_provider).__name__} "
            f"for provider '{auth_provider.id}'"
        )
