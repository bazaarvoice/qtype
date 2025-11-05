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

    def __init__(
        self,
        secret_name: str,
        context: str = "",
        cause: Exception | None = None,
    ):
        """
        Initialize SecretResolutionError with structured attributes.

        Args:
            secret_name: Name/ID/ARN of the secret that failed to resolve
            context: Optional context describing where resolution failed
                (e.g., "auth provider 'my_auth'", "step 'my_step'")
            cause: Optional underlying exception that caused the failure
        """
        self.secret_name = secret_name
        self.context = context
        self.cause = cause
        super().__init__(self._format_message())

    def _format_message(self) -> str:
        """Format the error message from structured attributes."""
        msg = f"Failed to resolve secret '{self.secret_name}'"
        if self.context:
            msg += f" in {self.context}"
        if self.cause:
            msg += f": {self.cause}"
        return msg
