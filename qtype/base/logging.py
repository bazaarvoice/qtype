"""Logging utilities for qtype."""

from __future__ import annotations

import logging


def configure_logging(
    level: str = "INFO", format_string: str | None = None
) -> None:
    """Configure root logging for qtype."""
    numeric_level = getattr(logging, level.upper(), logging.INFO)

    format_str = (
        format_string or "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    logging.basicConfig(
        level=numeric_level,
        format=format_str,
        force=True,  # Override any existing configuration
    )
