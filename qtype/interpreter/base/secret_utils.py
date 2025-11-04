"""
Utility functions for secret resolution.

This module provides centralized secret resolution functionality that can be
used throughout the interpreter layer. All secret resolution should use these
utilities to ensure consistent behavior and error handling.
"""

from __future__ import annotations

from typing import Any

from qtype.interpreter.base.exceptions import SecretResolutionError
from qtype.interpreter.base.secrets import SecretManagerBase
from qtype.semantic.model import SecretReference


def resolve_secret(
    value: str | SecretReference,
    secret_manager: SecretManagerBase | None,
    context: str = "",
) -> str:
    """
    Resolve a value that may be a string or a SecretReference.

    This is the canonical function for resolving secrets throughout the
    interpreter. All code that needs to resolve secrets should use this
    function to ensure consistent behavior and error messages.

    Args:
        value: Either a plain string or a SecretReference to resolve
        secret_manager: The secret manager instance to use for resolution,
            or None if no secret manager is configured
        context: Optional context string describing where the secret is
            being resolved (e.g., "step 'my_step'", "model 'gpt4'").
            This is included in error messages to aid debugging.

    Returns:
        The resolved string value. If value is already a string, it is
        returned unchanged. If value is a SecretReference, it is resolved
        using the secret manager.

    Raises:
        SecretResolutionError: If value is a SecretReference but no secret
            manager is provided, or if the secret manager fails to resolve
            the reference.

    Examples:
        >>> # Resolve a plain string (no-op)
        >>> resolve_secret("plain-text", None)
        'plain-text'

        >>> # Resolve a secret reference
        >>> ref = SecretReference(secret_name="my-app/api-key")
        >>> resolve_secret(ref, secret_manager, context="model 'gpt4'")
        'sk-abc123...'

        >>> # Error when secret manager is needed but not provided
        >>> resolve_secret(ref, None, context="model 'gpt4'")
        SecretResolutionError: Cannot resolve secret 'my-app/api-key'
            in model 'gpt4': no secret manager configured
    """
    if isinstance(value, str):
        return value

    if secret_manager is None:
        context_msg = f" in {context}" if context else ""
        raise SecretResolutionError(
            f"Cannot resolve secret '{value.secret_name}'{context_msg}: "
            "no secret manager configured. Please add a secret_manager "
            "to your application configuration."
        )

    try:
        return secret_manager(value)
    except Exception as e:
        context_msg = f" in {context}" if context else ""
        raise SecretResolutionError(
            f"Failed to resolve secret '{value.secret_name}'{context_msg}: {e}"
        ) from e


def resolve_secrets_in_dict(
    args: dict[str, Any],
    secret_manager: SecretManagerBase | None,
    context: str = "",
) -> dict[str, Any]:
    """
    Resolve any SecretReferences in a dictionary's values.

    This is a convenience function that iterates over a dictionary and
    resolves any values that might be SecretReferences. Non-secret values
    (strings, numbers, etc.) are passed through unchanged.

    Args:
        args: Dictionary with potentially secret-containing values
        secret_manager: The secret manager instance to use for resolution,
            or None if no secret manager is configured
        context: Optional context string describing where secrets are
            being resolved (e.g., "step 'my_step'", "index 'my_index'").
            This is included in error messages to aid debugging.

    Returns:
        A new dictionary with all SecretReferences resolved to strings.
        Other values are copied unchanged.

    Raises:
        SecretResolutionError: If any value is a SecretReference but no
            secret manager is provided, or if resolution fails.

    Examples:
        >>> args = {
        ...     "api_key": SecretReference(secret_name="my-app/key"),
        ...     "host": "api.example.com",
        ...     "port": 443
        ... }
        >>> resolve_secrets_in_dict(args, secret_manager, "tool 'my_api'")
        {'api_key': 'sk-abc123...', 'host': 'api.example.com', 'port': 443}
    """
    resolved = {}
    for key, value in args.items():
        # Check if value might be a SecretReference
        if isinstance(value, str) or hasattr(value, "secret_name"):
            resolved[key] = resolve_secret(value, secret_manager, context)
        else:
            resolved[key] = value
    return resolved
