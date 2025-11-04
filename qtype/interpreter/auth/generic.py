"""
Generic authorization context manager for QType interpreter.

This module provides a unified `auth()` context manager that handles any
AuthorizationProvider type and returns the appropriate session or provider
instance with secrets resolved.

Key Features:
- Automatic secret resolution for auth credentials using SecretManager
- Unified interface for all auth provider types (AWS, API Key, OAuth2)
- Returns authenticated sessions ready for use with external services

The context manager automatically:
1. Detects the auth provider type
2. Resolves any SecretReferences in credentials
3. Creates appropriate authentication sessions/objects
4. Handles cleanup when exiting the context

Supported Auth Types:
- AWSAuthProvider: Returns boto3.Session for AWS services
- APIKeyAuthProvider: Returns provider with resolved API key
- OAuth2AuthProvider: Returns provider with resolved client secret

Example:
    ```python
    from qtype.semantic.model import APIKeyAuthProvider, SecretReference
    from qtype.interpreter.auth.generic import auth

    # Auth with secret reference
    api_auth = APIKeyAuthProvider(
        id="openai",
        type="api_key",
        api_key=SecretReference(secret_name="my-app/openai-key")
    )

    with auth(api_auth, secret_manager) as provider:
        # provider.api_key contains the resolved secret
        headers = {"Authorization": f"Bearer {provider.api_key}"}
    ```
"""

from __future__ import annotations

from contextlib import contextmanager
from typing import Generator

import boto3  # type: ignore[import-untyped]

from qtype.interpreter.auth.aws import aws
from qtype.interpreter.base.secret_utils import resolve_secret
from qtype.interpreter.base.secrets import SecretManagerBase
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
    secret_manager: SecretManagerBase | None = None,
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
        # For API key providers, resolve the api_key and yield modified copy
        # The caller can access provider.api_key and provider.host
        context = f"auth provider '{auth_provider.id}'"
        resolved_key = resolve_secret(
            auth_provider.api_key, secret_manager, context
        )
        # Use model.copy(update=...) to create a copy with resolved secret
        resolved_provider = auth_provider.model_copy(
            update={"api_key": resolved_key}
        )
        yield resolved_provider

    elif isinstance(auth_provider, OAuth2AuthProvider):
        # OAuth2 - resolve client_secret
        context = f"auth provider '{auth_provider.id}'"
        resolved_secret = resolve_secret(
            auth_provider.client_secret, secret_manager, context
        )
        # Use model.copy(update=...) to create a copy with resolved secret
        resolved_provider = auth_provider.model_copy(
            update={"client_secret": resolved_secret}
        )
        yield resolved_provider

    else:
        # Unknown provider type
        raise UnsupportedAuthProviderError(
            f"Unsupported authorization provider type: "
            f"{type(auth_provider).__name__} "
            f"for provider '{auth_provider.id}'"
        )
