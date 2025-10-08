from __future__ import annotations

import logging
import uuid
from collections.abc import Callable, Generator, Iterable
from concurrent.futures import Future
from typing import Any

from qtype.interpreter.stream.chat.vercel import (
    ErrorChunk,
    FinishChunk,
    StartChunk,
    TextDeltaChunk,
    TextEndChunk,
    TextStartChunk,
)

logger = logging.getLogger(__name__)


def build_vercel_ai_formatter(
    stream_generator: Iterable[tuple[Any, Any]],
    result_future: Future,
    extract_text: Callable[[Any], str],
) -> Generator[str, None, None]:
    """
    Convert a low-level stream of (step, message) into Vercel AI UI protocol SSE.

    Args:
        stream_generator: Iterable yielding (step, message) pairs.
        result_future: Future representing completion of the flow.
        extract_text: Function to extract textual content from a message object.

    Yields:
        Lines formatted as 'data: {...}\\n\\n' for SSE.
    """
    start_chunk = StartChunk(messageId=str(uuid.uuid4()))  # type: ignore[arg-type]
    yield f"data: {start_chunk.model_dump_json(by_alias=True, exclude_none=True)}\n\n"

    text_id = str(uuid.uuid4())
    text_started = False

    for _step, message in stream_generator:
        try:
            content = extract_text(message)
        except Exception as exc:  # Defensive; continue streaming
            logger.debug(
                "Failed extracting text from message: %s", exc, exc_info=True
            )
            continue

        if not content or not content.strip():
            continue

        if not text_started:
            text_start = TextStartChunk(id=text_id)
            yield f"data: {text_start.model_dump_json(by_alias=True, exclude_none=True)}\n\n"
            text_started = True

        text_delta = TextDeltaChunk(id=text_id, delta=content)
        yield f"data: {text_delta.model_dump_json(by_alias=True, exclude_none=True)}\n\n"

    if text_started:
        text_end = TextEndChunk(id=text_id)
        yield f"data: {text_end.model_dump_json(by_alias=True, exclude_none=True)}\n\n"

    try:
        result_future.result(timeout=5.0)
        finish_chunk = FinishChunk()
        yield f"data: {finish_chunk.model_dump_json(by_alias=True, exclude_none=True)}\n\n"
    except Exception as exc:
        logger.error("Error finalizing flow execution: %s", exc, exc_info=True)
        error_chunk = ErrorChunk(errorText=str(exc))
        yield f"data: {error_chunk.model_dump_json(by_alias=True, exclude_none=True)}\n\n"
