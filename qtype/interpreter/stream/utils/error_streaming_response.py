from __future__ import annotations

from fastapi.responses import StreamingResponse

from qtype.interpreter.stream.chat.vercel import ErrorChunk


def error_streaming_response(message: str) -> StreamingResponse:
    """
    Create a streaming response with a single ErrorChunk.
    """
    error_chunk = ErrorChunk(errorText=message)
    response = StreamingResponse(
        [
            f"data: {error_chunk.model_dump_json(by_alias=True, exclude_none=True)}\n\n"
        ],
        media_type="text/plain; charset=utf-8",
    )
    response.headers["x-vercel-ai-ui-message-stream"] = "v1"
    return response
