from typing import Any


class InterpreterError(Exception):
    """Base exception class for ProtoGen interpreter errors."""

    def __init__(self, message: str, details: Any = None) -> None:
        super().__init__(message)
        self.message = message
        self.details = details
