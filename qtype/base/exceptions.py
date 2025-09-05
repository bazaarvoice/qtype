"""Base exceptions for qtype."""

from __future__ import annotations

from typing import Any


class QTypeError(Exception):
    """Base exception for all qtype errors."""

    def __init__(
        self, message: str, details: dict[str, Any] | None = None
    ) -> None:
        """Initialize the exception with message and optional details."""
        super().__init__(message)
        self.message = message
        self.details = details or {}


class ValidationError(QTypeError):
    """Exception raised when validation fails."""

    def __init__(
        self,
        message: str,
        errors: list[str] | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        """Initialize validation error with list of error messages."""
        super().__init__(message, details)
        self.errors = errors or []


class LoadError(QTypeError):
    """Exception raised when loading documents fails."""

    pass


class SemanticError(QTypeError):
    """Exception raised when semantic processing fails."""

    pass


class InterpreterError(QTypeError):
    """Exception raised when interpretation/execution fails."""

    pass
