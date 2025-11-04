"""
Custom exception types for the QType interpreter.

This module provides specialized exception classes for better error handling
and reporting throughout the interpreter layer.
"""

from __future__ import annotations


class SecretResolutionError(Exception):
    """
    Raised when a secret cannot be resolved.

    This exception is raised when attempting to resolve a SecretReference
    but the operation fails due to:
    - No secret manager configured
    - Secret not found in the secret store
    - Invalid secret format or structure
    - Authentication/authorization failures
    """

    pass


class AuthenticationError(Exception):
    """
    Raised when authentication operations fail.

    This includes failures in:
    - Creating authenticated sessions
    - Validating credentials
    - Refreshing authentication tokens
    """

    pass
