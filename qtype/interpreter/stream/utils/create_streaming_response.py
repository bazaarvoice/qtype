from __future__ import annotations

from collections.abc import Generator

from fastapi.responses import StreamingResponse


def create_streaming_response(
    formatter: Generator[str, None, None],
) -> StreamingResponse:
    """
    Wrap a formatter generator into a StreamingResponse with proper headers.
    """
    response = StreamingResponse(
        formatter, media_type="text/plain; charset=utf-8"
    )
    response.headers["x-vercel-ai-ui-message-stream"] = "v1"
    return response
