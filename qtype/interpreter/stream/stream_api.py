from __future__ import annotations

import logging
from typing import Any

from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from qtype.interpreter.flow import execute_flow
from qtype.interpreter.stream.utils import (
    build_vercel_ai_formatter,
    create_streaming_response,
    default_chat_extract_text,
    error_streaming_response,
)
from qtype.interpreter.streaming_helpers import create_streaming_generator
from qtype.semantic.model import Flow


class SimpleQuestionRequest(BaseModel):
    """
    Request model for single-turn question streaming.

    Attributes:
        id: Optional client-provided session/correlation identifier.
        question: The user question to execute against the flow.
    """

    prompt: str = Field(
        ...,
        title="question",
        json_schema_extra={"qtype_type": "text"},
    )


logger = logging.getLogger(__name__)

__all__ = ["create_stream_flow_endpoint"]


def create_stream_flow_endpoint(app: FastAPI, flow: Flow) -> None:
    flow_id = flow.id

    async def handle_question_stream(
        request: SimpleQuestionRequest,
    ) -> StreamingResponse:
        try:
            raw_question = request.prompt if request else None
            if not raw_question or not raw_question.strip():
                raise ValueError("A question is required in field 'prompt'.")

            flow_copy = flow.model_copy(deep=True)

            question_var = next(
                (
                    var
                    for var in flow_copy.inputs
                    if getattr(var, "id", "") == "question"
                ),
                None,
            )
            if question_var is None:
                question_var = next(
                    (
                        var
                        for var in flow_copy.inputs
                        if getattr(var, "type", None) in (str,)
                    ),
                    None,
                )
            if question_var is None:
                raise ValueError(
                    "Flow does not define a suitable 'question' text input variable."
                )

            question_var.value = raw_question.strip()

            execution_kwargs: dict[str, Any] = {
                "conversation_history": [],
            }
            stream_generator, result_future = create_streaming_generator(
                execute_flow, flow_copy, **execution_kwargs
            )
        except ValueError as ve:
            logger.debug("Validation error preparing question stream: %s", ve)
            return error_streaming_response(str(ve))
        except Exception as exc:
            logger.error(
                "Unexpected error preparing question stream: %s",
                exc,
                exc_info=True,
            )
            return error_streaming_response("Internal error.")

        formatter = build_vercel_ai_formatter(
            stream_generator=stream_generator,
            result_future=result_future,
            extract_text=default_chat_extract_text,
        )
        return create_streaming_response(formatter)

    app.post(
        f"/flows/{flow_id}/stream",
        tags=["stream"],
        summary=f"Stream {flow_id} flow output (single question)",
        description=flow.description,
        response_class=StreamingResponse,
    )(handle_question_stream)
