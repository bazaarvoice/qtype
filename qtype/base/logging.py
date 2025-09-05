"""Logging utilities for qtype."""

from __future__ import annotations

import logging


def get_logger(name: str) -> logging.Logger:
    """Get a logger with the given name and consistent formatting."""
    logger = logging.getLogger(f"qtype.{name}")

    # Only configure if not already configured
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)

    return logger


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
