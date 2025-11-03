"""
Generic authorization context manager for QType interpreter.

This module provides a unified context manager that can handle any AuthorizationProvider
type and return the appropriate session or provider instance.
"""

from __future__ import annotations

from contextlib import contextmanager
from typing import TYPE_CHECKING, Any, Generator

import boto3  # type: ignore[import-untyped]

from qtype.interpreter.auth.aws import aws
from qtype.semantic.model import (
    APIKeyAuthProvider,
    AuthorizationProvider,
    AWSAuthProvider,
    OAuth2AuthProvider,
    SecretReference,
)

if TYPE_CHECKING:
    pass


def _resolve_secret(value: str | SecretReference, secret_manager: Any) -> str:
    """Resolve a secret value if it's a SecretReference."""
    if isinstance(value, str):
        return value
    if secret_manager is None:
        raise RuntimeError(
            "Cannot resolve SecretReference without a secret manager configured."
        )
    return secret_manager(value)


class UnsupportedAuthProviderError(Exception):
    """Raised when an unsupported authorization provider type is used."""

    pass


@contextmanager
def auth(
    auth_provider: AuthorizationProvider,
    secret_manager: Any = None,
) -> Generator[
    boto3.Session | APIKeyAuthProvider | OAuth2AuthProvider, None, None
]:
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
        with aws(auth_provider, secret_manager) as session:
            yield session

    elif isinstance(auth_provider, APIKeyAuthProvider):
        # For API key providers, resolve the api_key and return the provider
        # The caller can access provider.api_key and provider.host
        resolved_key = _resolve_secret(auth_provider.api_key, secret_manager)  # type: ignore[arg-type]
        # Create a copy with resolved api_key
        resolved_provider = APIKeyAuthProvider(
            id=auth_provider.id,
            type=auth_provider.type,
            api_key=resolved_key,
            host=auth_provider.host,
        )
        yield resolved_provider

    elif isinstance(auth_provider, OAuth2AuthProvider):
        # OAuth2 - resolve client_secret
        resolved_secret = _resolve_secret(
            auth_provider.client_secret,
            secret_manager,  # type: ignore[arg-type]
        )
        # Create a copy with resolved client_secret
        resolved_provider = OAuth2AuthProvider(
            id=auth_provider.id,
            type=auth_provider.type,
            client_id=auth_provider.client_id,
            client_secret=resolved_secret,
            token_url=auth_provider.token_url,
        )
        yield resolved_provider

    else:
        # Unknown provider type
        raise UnsupportedAuthProviderError(
            f"Unsupported authorization provider type: {type(auth_provider).__name__} "
            f"for provider '{auth_provider.id}'"
        )
