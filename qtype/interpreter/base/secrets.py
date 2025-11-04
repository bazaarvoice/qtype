"""
Base class for secret manager implementations.

This module provides an abstract base class for secret managers that
resolve SecretReference objects at runtime.
"""

from __future__ import annotations

import json
from abc import ABC, abstractmethod

from qtype.semantic.model import (
    AWSAuthProvider,
    AWSSecretManager,
    SecretManager,
    SecretReference,
)


class SecretManagerBase(ABC):
    """
    Abstract base class for secret manager implementations.

    Secret managers are responsible for resolving SecretReference objects
    into actual secret values at runtime. Each implementation corresponds
    to a specific secret management service (e.g., AWS Secrets Manager,
    Kubernetes Secrets, HashiCorp Vault).
    """

    @abstractmethod
    def __call__(self, secret_ref: SecretReference) -> str:
        """
        Resolve a secret reference and return the secret value.

        Args:
            secret_ref: SecretReference containing the secret identifier
                and optional key for accessing specific fields

        Returns:
            str: The resolved secret value

        Raises:
            Exception: If the secret cannot be retrieved or resolved
        """
        pass


class AWSSecretManagerError(Exception):
    """Raised when AWS Secrets Manager operations fail."""

    pass


class AWSSecretManagerImpl(SecretManagerBase):
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
            AWSSecretManager,
            AWSAuthProvider,
            SecretReference
        )
        from qtype.interpreter.secrets.aws import AWSSecretManagerImpl

        # Create auth provider
        auth = AWSAuthProvider(
            id="my-aws-auth",
            type="aws",
            profile_name="default",
            region="us-east-1"
        )

        # Create secret manager config
        secret_mgr_config = AWSSecretManager(
            id="my-secret-manager",
            type="aws_secret_manager",
            auth=auth
        )

        # Create implementation
        secret_mgr = AWSSecretManagerImpl(secret_mgr_config)

        # Resolve a secret
        secret_ref = SecretReference(
            secret_name="my-app/api-key",
            key=None
        )
        api_key = secret_mgr(secret_ref)
        ```
    """

    def __init__(self, config: AWSSecretManager):
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

    def __call__(self, secret_ref: SecretReference) -> str:
        """
        Resolve a secret reference from AWS Secrets Manager.

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
    config: SecretManager | None,
) -> SecretManagerBase | None:
    """
    Factory function to create the appropriate secret manager implementation.

    Args:
        config: SecretManager configuration from semantic model, or None

    Returns:
        SecretManagerBase: Appropriate implementation based on config type,
            or None if config is None

    Raises:
        ValueError: If the secret manager type is not supported

    Example:
        ```python
        from qtype.semantic.model import AWSSecretManager, AWSAuthProvider
        from qtype.interpreter.base.secrets import create_secret_manager

        # Create config
        config = AWSSecretManager(
            id="my-secret-manager",
            type="aws_secret_manager",
            auth=auth_provider
        )

        # Create implementation
        secret_manager = create_secret_manager(config)

        # Use it
        secret_value = secret_manager(secret_ref)
        ```
    """
    if config is None:
        return None

    if isinstance(config, AWSSecretManager):
        return AWSSecretManagerImpl(config)

    raise ValueError(
        f"Unsupported secret manager type: {config.type}. "
        f"Supported types: aws_secret_manager"
    )
