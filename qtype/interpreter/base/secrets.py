"""
Base class for secret manager implementations.

This module provides an abstract base class for secret managers that
resolve SecretReference objects at runtime.
"""

from __future__ import annotations

import json
from abc import ABC, abstractmethod
from typing import Any

from qtype.interpreter.base.exceptions import SecretResolutionError
from qtype.semantic.model import AWSAuthProvider
from qtype.semantic.model import AWSSecretManager as AWSSecretManagerConfig
from qtype.semantic.model import SecretManager as SecretManagerConfig
from qtype.semantic.model import SecretReference


class SecretManagerBase(ABC):
    """
    Abstract base class for secret manager implementations.

    Secret managers are responsible for resolving SecretReference objects
    into actual secret values at runtime. Each implementation corresponds
    to a specific secret management service (e.g., AWS Secrets Manager,
    Kubernetes Secrets, HashiCorp Vault).
    """

    @abstractmethod
    def get_secret(self, secret_ref: SecretReference) -> str:
        """
        Retrieve a secret value from the underlying secret store.

        Subclasses must implement this method to interface with their
        specific secret management service.

        Args:
            secret_ref: SecretReference containing the secret identifier
                and optional key for accessing specific fields

        Returns:
            str: The resolved secret value

        Raises:
            Exception: If the secret cannot be retrieved or resolved
        """
        pass

    def __call__(self, value: str | SecretReference, context: str = "") -> str:
        """
        Resolve a value that may be a string or a SecretReference.

        This is the main entry point for secret resolution. It handles
        plain strings (pass-through) and SecretReferences (delegates to
        get_secret()).

        Args:
            value: Either a plain string or a SecretReference to resolve
            context: Optional context string describing where the secret
                is being resolved (e.g., "step 'my_step'", "model 'gpt4'").
                This is included in error messages to aid debugging.

        Returns:
            The resolved string value. If value is already a string, it is
            returned unchanged. If value is a SecretReference, it is
            resolved using get_secret().

        Raises:
            SecretResolutionError: If secret resolution fails

        Examples:
            >>> # Resolve a plain string (no-op)
            >>> secret_manager("plain-text")
            'plain-text'

            >>> # Resolve a secret reference
            >>> ref = SecretReference(secret_name="my-app/api-key")
            >>> secret_manager(ref, context="model 'gpt4'")
            'sk-abc123...'
        """
        if isinstance(value, str):
            return value

        try:
            return self.get_secret(value)
        except Exception as e:
            raise SecretResolutionError(
                secret_name=value.secret_name, context=context, cause=e
            ) from e

    def resolve_secrets_in_dict(
        self, args: dict[str, Any], context: str = ""
    ) -> dict[str, Any]:
        """
        Resolve any SecretReferences in a dictionary's values.

        This is a convenience method that iterates over a dictionary and
        resolves any values that might be SecretReferences. Non-secret
        values (strings, numbers, etc.) are passed through unchanged.

        Args:
            args: Dictionary with potentially secret-containing values
            context: Optional context string describing where secrets are
                being resolved (e.g., "step 'my_step'", "index 'my_index'").
                This is included in error messages to aid debugging.

        Returns:
            A new dictionary with all SecretReferences resolved to strings.
            Other values are copied unchanged.

        Raises:
            SecretResolutionError: If resolution fails for any secret.

        Examples:
            >>> args = {
            ...     "api_key": SecretReference(secret_name="my-app/key"),
            ...     "host": "api.example.com",
            ...     "port": 443
            ... }
            >>> secret_manager.resolve_secrets_in_dict(
            ...     args, "tool 'my_api'"
            ... )
            {'api_key': 'sk-abc123...', 'host': 'api.example.com', 'port': 443}
        """
        resolved = {}
        for key, value in args.items():
            # Check if value might be a SecretReference
            if isinstance(value, str) or hasattr(value, "secret_name"):
                resolved[key] = self(value, context)
            else:
                resolved[key] = value
        return resolved


class AWSSecretManagerError(Exception):
    """Raised when AWS Secrets Manager operations fail."""

    pass


class NoOpSecretManager(SecretManagerBase):
    """
    No-op secret manager that always raises an error.

    This implementation is used when no secret manager is configured.
    It allows code to always have a valid SecretManagerBase instance
    instead of dealing with Optional types, following the Null Object
    pattern.

    Any attempt to resolve a secret will raise a SecretResolutionError
    with a helpful message explaining that no secret manager is configured.
    """

    def get_secret(self, secret_ref: SecretReference) -> str:
        """
        Raise an error indicating no secret manager is configured.

        Args:
            secret_ref: The SecretReference that cannot be resolved

        Raises:
            SecretResolutionError: Always raised with configuration help
        """
        raise SecretResolutionError(
            secret_name=secret_ref.secret_name,
            context="no secret manager configured",
            cause=ValueError(
                "Please add a secret_manager to your application configuration"
            ),
        )


class AWSSecretManager(SecretManagerBase):
    """
    AWS Secrets Manager implementation.

    This class uses boto3 to retrieve secrets from AWS Secrets Manager.
    It supports both string secrets and JSON secrets with optional key
    extraction.

    The implementation uses the existing auth library to authenticate
    with AWS and caches the boto3 session for efficient reuse.

    Example:
        ```python
        from qtype.semantic.model import (
            AWSSecretManager as AWSSecretManagerConfig,
            AWSAuthProvider,
            SecretReference
        )
        from qtype.interpreter.base.secrets import AWSSecretManager

        # Create auth provider
        auth = AWSAuthProvider(
            id="my-aws-auth",
            type="aws",
            profile_name="default",
            region="us-east-1"
        )

        # Create secret manager config
        secret_mgr_config = AWSSecretManagerConfig(
            id="my-secret-manager",
            type="aws_secret_manager",
            auth=auth
        )

        # Create implementation
        secret_mgr = AWSSecretManager(secret_mgr_config)

        # Resolve a secret
        secret_ref = SecretReference(
            secret_name="my-app/api-key",
            key=None
        )
        api_key = secret_mgr(secret_ref)
        ```
    """

    def __init__(self, config: AWSSecretManagerConfig):
        """
        Initialize AWS Secrets Manager implementation.

        Args:
            config: AWSSecretManager configuration from semantic model
        """
        if not isinstance(config.auth, AWSAuthProvider):
            raise AWSSecretManagerError(
                f"AWSSecretManager requires AWSAuthProvider, got "
                f"{type(config.auth).__name__}"
            )
        self.config = config

    def get_secret(self, secret_ref: SecretReference) -> str:
        """
        Retrieve a secret from AWS Secrets Manager.

        This method retrieves the secret value from AWS Secrets Manager
        using the secret name provided in the reference. If the secret
        is a JSON object and a key is specified, it extracts that
        specific key's value.

        Args:
            secret_ref: SecretReference containing the secret name and
                optional key

        Returns:
            str: The resolved secret value

        Raises:
            AWSSecretManagerError: If auth provider is wrong type
            ClientError: If AWS API call fails
            json.JSONDecodeError: If secret is not valid JSON when key
                is specified
        """
        from qtype.interpreter.auth.aws import aws

        with aws(self.config.auth) as session:  # type: ignore
            client = session.client("secretsmanager")
            response = client.get_secret_value(SecretId=secret_ref.secret_name)

            if "SecretString" not in response:
                raise AWSSecretManagerError(
                    f"Secret '{secret_ref.secret_name}' contains binary "
                    "data, which is not supported"
                )

            secret_value: str = response["SecretString"]

            if not secret_ref.key:
                return secret_value

            # Parse JSON and extract key
            secret_dict = json.loads(secret_value)
            if not isinstance(secret_dict, dict):
                raise AWSSecretManagerError(
                    f"Secret '{secret_ref.secret_name}' is not a JSON "
                    f"object, cannot extract key '{secret_ref.key}'"
                )

            if secret_ref.key not in secret_dict:
                raise AWSSecretManagerError(
                    f"Key '{secret_ref.key}' not found in secret "
                    f"'{secret_ref.secret_name}'"
                )

            return str(secret_dict[secret_ref.key])


def create_secret_manager(
    config: SecretManagerConfig | None,
) -> SecretManagerBase:
    """
    Factory function to create the appropriate secret manager implementation.

    Args:
        config: SecretManager configuration from semantic model, or None

    Returns:
        SecretManagerBase: Appropriate implementation based on config type.
            Returns NoOpSecretManager if config is None.

    Raises:
        ValueError: If the secret manager type is not supported

    Example:
        ```python
        from qtype.semantic.model import (
            AWSSecretManager as AWSSecretManagerConfig,
            AWSAuthProvider
        )
        from qtype.interpreter.base.secrets import create_secret_manager

        # Create config
        config = AWSSecretManagerConfig(
            id="my-secret-manager",
            type="aws_secret_manager",
            auth=auth_provider
        )

        # Create implementation
        secret_manager = create_secret_manager(config)

        # Use it directly - no None checks needed!
        secret_value = secret_manager(secret_ref)
        ```
    """
    if config is None:
        return NoOpSecretManager()

    if isinstance(config, AWSSecretManagerConfig):
        return AWSSecretManager(config)

    raise ValueError(
        f"Unsupported secret manager type: {config.type}. "
        f"Supported types: aws_secret_manager"
    )
