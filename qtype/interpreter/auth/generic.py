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


def resolve_provider_secrets(
    provider: AuthorizationProvider,
    secret_manager: SecretManagerBase,
) -> AuthorizationProvider:
    """
    Resolve all SecretReference fields in an auth provider.

    This helper automatically detects and resolves any fields that contain
    SecretReference objects, returning a copy of the provider with resolved
    secret values. This eliminates duplication when handling different auth
    provider types.

    Note: Always returns a copy to ensure consistency, even when there are
    no secrets to resolve. This prevents issues with object identity checks
    in tests and ensures a clean separation between DSL and runtime objects.

    Args:
        provider: Auth provider instance with potential SecretReferences
        secret_manager: Secret manager to use for resolution

    Returns:
        Copy of the provider with all SecretReferences resolved to strings

    Example:
        >>> provider = APIKeyAuthProvider(
        ...     id="my_auth",
        ...     api_key=SecretReference(secret_name="my-key")
        ... )
        >>> resolved = resolve_provider_secrets(provider, secret_manager)
        >>> assert isinstance(resolved.api_key, str)
    """
    context = f"auth provider '{provider.id}'"
    updates = {}

    # Iterate over all fields and resolve any SecretReferences
    for field_name, field_info in provider.model_fields.items():
        value = getattr(provider, field_name)
        # Check if value is a SecretReference by looking for secret_name attr
        if hasattr(value, "secret_name"):
            updates[field_name] = secret_manager(value, context)

    # Always create a copy to ensure clean separation between DSL and runtime
    return provider.model_copy(update=updates)


@contextmanager
def auth(
    auth_provider: AuthorizationProvider,
    secret_manager: SecretManagerBase,
) -> Generator[boto3.Session | AuthorizationProvider, None, None]:
    """
    Create an appropriate session or provider instance based on the auth provider type.

    This context manager dispatches to the appropriate authentication handler based
    on the type of AuthorizationProvider:
    - AWSAuthProvider: Returns a configured boto3.Session
    - APIKeyAuthProvider: Returns the provider instance (contains the API key)

    Args:
        auth_provider: AuthorizationProvider instance of any supported type
        secret_manager: Secret manager for resolving SecretReferences

    Yields:
        boto3.Session | APIKeyAuthProvider: The appropriate session or provider instance

    Raises:
        UnsupportedAuthProviderError: When an unsupported provider type is used

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

    elif isinstance(auth_provider, (APIKeyAuthProvider, OAuth2AuthProvider)):
        # For non-AWS providers, resolve secrets and yield modified copy
        resolved_provider = resolve_provider_secrets(
            auth_provider, secret_manager
        )
        yield resolved_provider

    else:
        # Unknown provider type
        raise UnsupportedAuthProviderError(
            f"Unsupported authorization provider type: "
            f"{type(auth_provider).__name__} "
            f"for provider '{auth_provider.id}'"
        )
