import logging
from typing import Any, Callable

from llama_cloud import MessageRole as LlamaMessageRole
from llama_index.core.base.llms.types import ChatResponse, CompletionResponse

from qtype.dsl.base_types import PrimitiveTypeEnum
from qtype.dsl.domain_types import (
    ChatContent,
    ChatMessage,
    Embedding,
    MessageRole,
)
from qtype.interpreter.conversions import (
    from_chat_message,
    to_chat_message,
    to_embedding_model,
    to_llm,
    to_memory,
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
        stream_fn: Optional streaming callback function.
        **kwargs: Additional keyword arguments including conversation_history.
    """
    logger.debug(f"Executing LLM inference step: {li.id}")

    # Ensure we only have one output variable set.
    if len(li.outputs) != 1:
        raise InterpreterError(
            "LLMInference step must have exactly one output variable."
        )
    output_variable = li.outputs[0]

    # Determine if this is a chat session, completion, or embedding inference
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

        # Current user input
        inputs = [
            to_chat_message(input.value)  # type: ignore
            for input in li.inputs
        ]

        # The session id is used to isolate the memory from other "users"
        session_id = kwargs.get("session_id")

        # If memory is defined, use it.
        if li.memory:
            memory = to_memory(session_id, li.memory)

            from llama_index.core.async_utils import asyncio_run

            # add the inputs to the memory
            asyncio_run(memory.aput_messages(inputs))
            # Use the whole memory state as inputs to the llm
            inputs = memory.get_all()
        else:
            # If memory is not defined, see if a conversation history was provided.
            # This is the list of messages from the front end
            conversation_history = kwargs.get("conversation_history", [])  # type: ignore
            if not isinstance(conversation_history, list):
                raise ValueError(
                    "Unexpected error: conversation history is not a list."
                )
            history: list[ChatMessage] = conversation_history
            inputs = [to_chat_message(msg) for msg in history] + inputs

        if li.system_message and inputs[0].role != LlamaMessageRole.SYSTEM:
            # There is a system prompt we should append
            # Note system_prompt on the llm doesn't work for chat -- is only used for predict https://github.com/run-llama/llama_index/issues/13983
            system_message = ChatMessage(
                role=MessageRole.system,
                blocks=[
                    ChatContent(
                        type=PrimitiveTypeEnum.text,
                        content=li.system_message,
                    )
                ],
            )
            inputs = [to_chat_message(system_message)] + inputs

        # If the stream function is set, we'll stream the results
        chat_result: ChatResponse
        if stream_fn:
            generator = model.stream_chat(
                messages=inputs,
                **(
                    li.model.inference_params
                    if li.model.inference_params
                    else {}
                ),
            )
            for chat_response in generator:
                stream_fn(li, chat_response.delta)
            # Get the final result for processing
            chat_result = chat_response  # Use the last result from streaming
        else:
            chat_result = model.chat(
                messages=inputs,
                **(
                    li.model.inference_params
                    if li.model.inference_params
                    else {}
                ),
            )
        output_variable.value = from_chat_message(chat_result.message)
        if li.memory:
            memory.put(chat_result.message)
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

        complete_result: CompletionResponse
        complete_reasoning: str = ""

        if stream_fn:
            generator = model.stream_complete(prompt=input)
            for complete_result in generator:
                raw = complete_result.raw  # this is temporary for development - TODO: extract reasoning better or find more appropriate place 
                reasonring_text = raw.get("contentBlockDelta", {}).get("delta", {}).get("reasoningContent", {}).get("text")
                if reasonring_text:
                    complete_reasoning = complete_reasoning + reasonring_text
                stream_fn(li, complete_result.delta)
        else:
            complete_result = model.complete(prompt=input)
        print('complete_reasoning: ', complete_reasoning)
        output_variable.value = complete_result.text
    return li.outputs  # type: ignore[return-value]
