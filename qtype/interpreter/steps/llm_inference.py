import logging
from typing import Any, Callable

from llama_index.core.base.llms.types import ChatResponse, CompletionResponse

from qtype.dsl.domain_types import ChatMessage, Embedding
from qtype.interpreter.conversions import (
    from_chat_message,
    to_chat_message,
    to_embedding_model,
    to_llm,
)
from qtype.interpreter.exceptions import InterpreterError
from qtype.semantic.model import EmbeddingModel, LLMInference, Variable

logger = logging.getLogger(__name__)


def execute(
    li: LLMInference,
    stream_fn: Callable | None = None,
    **kwargs: dict[Any, Any],
) -> list[Variable]:
    """Execute a LLM inference step.

    Args:
        li: The LLM inference step to execute.
        **kwargs: Additional keyword arguments.
    """
    logger.debug(f"Executing LLM inference step: {li.id}")

    if len(li.outputs) != 1:
        raise InterpreterError(
            "LLMInference step must have exactly one output variable."
        )
    output_variable = li.outputs[0]

    if output_variable.type == Embedding:
        if not isinstance(li.model, EmbeddingModel):
            raise InterpreterError(
                f"LLMInference step with Embedding output must use an embedding model, got {type(li.model)}"
            )
        if len(li.inputs) != 1:
            raise InterpreterError(
                "LLMInference step for completion must have exactly one input variable."
            )

        input = li.inputs[0].value
        model = to_embedding_model(li.model)
        result = model.get_text_embedding(text=input)
        output_variable.value = Embedding(
            vector=result,
            source_text=input if isinstance(input, str) else None,
            metadata=None,
        )
    elif output_variable.type == ChatMessage:
        model = to_llm(li.model, li.system_message)

        if not all(
            isinstance(input.value, ChatMessage) for input in li.inputs
        ):
            raise InterpreterError(
                f"LLMInference step with ChatMessage output must have ChatMessage inputs. Got {li.inputs}"
            )
        # TODO: Add Memory
        if any(not input.is_set() for input in li.inputs):
            raise InterpreterError(
                f"All inputs to LLMInference step must be set. Inputs were: {li.inputs}."
            )
        inputs = [
            to_chat_message(input.value)  # type: ignore
            for input in li.inputs
            if input.is_set()
        ]  # type: ignore

        if stream_fn:
            generator = model.stream_chat(
                messages=inputs,
                **(
                    li.model.inference_params
                    if li.model.inference_params
                    else {}
                ),
            )
            for chatResult in generator:
                stream_fn(li, chatResult.message)
        else:
            chatResult: ChatResponse = model.chat(
                messages=inputs,
                **(
                    li.model.inference_params
                    if li.model.inference_params
                    else {}
                ),
            )
        output_variable.value = from_chat_message(chatResult.message)
    else:
        model = to_llm(li.model, li.system_message)

        if len(li.inputs) != 1:
            raise InterpreterError(
                "LLMInference step for completion must have exactly one input variable."
            )

        input = li.inputs[0].value
        if not isinstance(input, str):
            logger.warning(
                f"Input to LLMInference step {li.id} is not a string, converting: {input}"
            )
            input = str(input)

        if stream_fn:
            generator = model.stream_complete(prompt=input)
            for completeResult in generator:
                stream_fn(li, completeResult.delta)
        else:
            completeResult: CompletionResponse = model.complete(prompt=input)
        output_variable.value = completeResult.text

    return li.outputs  # type: ignore[return-value]
