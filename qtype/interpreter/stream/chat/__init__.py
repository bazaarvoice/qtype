"""
Stream and chat utilities for QType interpreter.

This package provides conversions between QType's internal streaming
events and external chat protocols like Vercel AI SDK.
"""

from __future__ import annotations

from qtype.interpreter.stream.chat.converter import (
    StreamEventConverter,
    format_stream_events_as_sse,
)

__all__ = ["StreamEventConverter", "format_stream_events_as_sse"]
