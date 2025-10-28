from typing import AsyncIterator

from llama_cloud import MessageRole as LlamaMessageRole
from llama_index.core.base.llms.types import ChatResponse, CompletionResponse
from openinference.semconv.trace import OpenInferenceSpanKindValues

from qtype.base.types import PrimitiveTypeEnum
from qtype.dsl.domain_types import ChatContent, ChatMessage, MessageRole
from qtype.interpreter.base.base_step_executor import StepExecutor
from qtype.interpreter.conversions import (
    from_chat_message,
    to_chat_message,
    to_llm,
    to_memory,
)
from qtype.interpreter.types import FlowMessage
from qtype.semantic.model import LLMInference


class LLMInferenceExecutor(StepExecutor):
    """Executor for LLMInference steps."""

    # LLM inference spans should be marked as LLM type
    span_kind = OpenInferenceSpanKindValues.LLM

    def __init__(self, step: LLMInference, **dependencies):
        super().__init__(step, **dependencies)
        if not isinstance(step, LLMInference):
            raise ValueError(
                "LLMInferenceExecutor can only execute LLMInference steps."
            )
        self.step: LLMInference = step

    async def process_message(
        self,
        message: FlowMessage,
    ) -> AsyncIterator[FlowMessage]:
        """Process a single FlowMessage for the LLMInference step.

        Args:
            message: The FlowMessage to process.

        Yields:
            FlowMessage with the results of LLM inference.
        """
        # Get output variable info
        output_variable_id = self.step.outputs[0].id
        output_variable_type = self.step.outputs[0].type

        try:
            # Determine if this is a chat or completion inference
            if output_variable_type == ChatMessage:
                result_message = await self._process_chat(
                    message, output_variable_id
                )
            else:
                result_message = await self._process_completion(
                    message, output_variable_id
                )

            yield result_message

        except Exception as e:
            message.set_error(self.step.id, e)
            yield message

    async def _process_chat(
        self,
        message: FlowMessage,
        output_variable_id: str,
    ) -> FlowMessage:
        """Process a chat inference request.

        Args:
            message: The FlowMessage to process.
            output_variable_id: The ID of the output variable.

        Returns:
            FlowMessage with the chat response.
        """
        model = to_llm(self.step.model, self.step.system_message)

        # Convert input variables to chat messages
        inputs = []
        for input_var in self.step.inputs:
            value = message.variables.get(input_var.id)
            if value and isinstance(value, ChatMessage):
                inputs.append(to_chat_message(value))

        # Get session ID for memory isolation
        session_id = message.session.session_id

        # If memory is defined, use it
        if self.step.memory:
            memory = to_memory(session_id, self.step.memory)

            # Add the inputs to the memory
            from llama_index.core.async_utils import asyncio_run

            asyncio_run(memory.aput_messages(inputs))
            # Use the whole memory state as inputs to the llm
            inputs = memory.get_all()
        else:
            # If memory is not defined, use conversation history from session
            conversation_history = (
                message.session.conversation_history
                if hasattr(message.session, "conversation_history")
                else []
            )
            if conversation_history:
                inputs = [
                    to_chat_message(msg) for msg in conversation_history
                ] + inputs

        # Add system message if needed
        if (
            self.step.system_message
            and inputs
            and inputs[0].role != LlamaMessageRole.SYSTEM
        ):
            system_message = ChatMessage(
                role=MessageRole.system,
                blocks=[
                    ChatContent(
                        type=PrimitiveTypeEnum.text,
                        content=self.step.system_message,
                    )
                ],
            )
            inputs = [to_chat_message(system_message)] + inputs

        # Perform inference with streaming if callback provided
        chat_result: ChatResponse
        if self.on_stream_event:
            # Generate a unique stream ID for this inference
            stream_id = f"llm-{self.step.id}-{id(message)}"

            async with self.stream_emitter.text_stream(stream_id) as streamer:
                generator = model.stream_chat(
                    messages=inputs,
                    **(
                        self.step.model.inference_params
                        if self.step.model.inference_params
                        else {}
                    ),
                )
                for chat_response in generator:
                    await streamer.delta(chat_response.delta)
            # Get the final result
            chat_result = chat_response
        else:
            chat_result = model.chat(
                messages=inputs,
                **(
                    self.step.model.inference_params
                    if self.step.model.inference_params
                    else {}
                ),
            )

        # Store result in memory if configured
        if self.step.memory:
            memory.put(chat_result.message)

        # Convert result and return
        result_value = from_chat_message(chat_result.message)
        return message.copy_with_variables({output_variable_id: result_value})

    async def _process_completion(
        self,
        message: FlowMessage,
        output_variable_id: str,
    ) -> FlowMessage:
        """Process a completion inference request.

        Args:
            message: The FlowMessage to process.
            output_variable_id: The ID of the output variable.

        Returns:
            FlowMessage with the completion response.
        """
        model = to_llm(self.step.model, self.step.system_message)

        # Get input value
        input_value = message.variables.get(self.step.inputs[0].id)
        if not isinstance(input_value, str):
            input_value = str(input_value)

        # Perform inference with streaming if callback provided
        complete_result: CompletionResponse
        if self.on_stream_event:
            # Generate a unique stream ID for this inference
            stream_id = f"llm-{self.step.id}-{id(message)}"

            async with self.stream_emitter.text_stream(stream_id) as streamer:
                generator = model.stream_complete(
                    prompt=input_value,
                    **(
                        self.step.model.inference_params
                        if self.step.model.inference_params
                        else {}
                    ),
                )
                for complete_response in generator:
                    await streamer.delta(complete_response.delta)
            # Get the final result
            complete_result = complete_response
        else:
            complete_result = model.complete(
                prompt=input_value,
                **(
                    self.step.model.inference_params
                    if self.step.model.inference_params
                    else {}
                ),
            )

        # Return result
        return message.copy_with_variables(
            {output_variable_id: complete_result.text}
        )
