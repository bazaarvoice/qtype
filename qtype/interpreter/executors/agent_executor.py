from __future__ import annotations

import logging
from typing import Any, AsyncIterator, cast

from llama_index.core.agent import ReActAgent
from openinference.semconv.trace import OpenInferenceSpanKindValues

from qtype.base.types import PrimitiveTypeEnum
from qtype.dsl.domain_types import ChatContent, ChatMessage, MessageRole
from qtype.interpreter.base.base_step_executor import StepExecutor
from qtype.interpreter.base.executor_context import ExecutorContext
from qtype.interpreter.conversions import to_chat_message, to_llm, to_memory
from qtype.interpreter.executors.invoke_tool_executor import ToolExecutionMixin
from qtype.interpreter.tools import FunctionToolHelper
from qtype.interpreter.types import FlowMessage
from qtype.semantic.model import Agent, APITool, PythonFunctionTool

logger = logging.getLogger(__name__)


class AgentExecutor(StepExecutor, ToolExecutionMixin, FunctionToolHelper):
    """Executor for Agent steps using LlamaIndex ReActAgent."""

    # Agent execution should be marked as AGENT type (similar to LLM)
    span_kind = OpenInferenceSpanKindValues.AGENT

    def __init__(self, step: Agent, context: ExecutorContext, **dependencies):
        super().__init__(step, context, **dependencies)
        if not isinstance(step, Agent):
            raise ValueError("AgentExecutor can only execute Agent steps.")
        self.step: Agent = step
        self._agent = self._create_agent()

    def _create_agent(self) -> ReActAgent:
        """Create the ReActAgent instance.

        Returns:
            Configured ReActAgent instance.
        """
        # Convert QType tools to LlamaIndex FunctionTools
        llama_tools = [
            self._create_function_tool(
                cast(APITool | PythonFunctionTool, tool)
            )
            for tool in self.step.tools
        ]

        # Get the LLM for the agent
        llm = to_llm(
            self.step.model, self.step.system_message, self._secret_manager
        )

        # Create ReActAgent
        return ReActAgent(
            name=self.step.id,
            description=f"Agent for step {self.step.id}",
            system_prompt=self.step.system_message,
            tools=llama_tools,  # type: ignore[arg-type]
            llm=llm,
        )

    async def process_message(
        self,
        message: FlowMessage,
    ) -> AsyncIterator[FlowMessage]:
        """Process a single FlowMessage for the Agent step.

        Args:
            message: The FlowMessage to process.

        Yields:
            FlowMessage with agent execution results.
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
            logger.error(f"Agent execution failed: {e}", exc_info=True)
            # Emit error event to stream so frontend can display it
            await self.stream_emitter.error(str(e))
            message.set_error(self.step.id, e)
            yield message

    async def _process_chat(
        self,
        message: FlowMessage,
        output_variable_id: str,
    ) -> FlowMessage:
        """Process a chat-based agent request.

        Args:
            message: The FlowMessage to process.
            output_variable_id: The ID of the output variable.

        Returns:
            FlowMessage with the agent chat response.
        """
        # Convert input variables to chat messages
        inputs = []
        for input_var in self.step.inputs:
            value = message.variables.get(input_var.id)
            if value and isinstance(value, ChatMessage):
                inputs.append(to_chat_message(value))

        # Get session ID for memory isolation
        session_id = message.session.session_id

        # Handle memory if configured
        if self.step.memory:
            memory = to_memory(session_id, self.step.memory)

            # Add the inputs to the memory
            await memory.aput_messages(inputs)
            # Use the whole memory state as inputs
            inputs = memory.get_all()
        else:
            # Use conversation history from session if no memory
            conversation_history = getattr(
                message.session, "conversation_history", []
            )
            if conversation_history:
                inputs = [
                    to_chat_message(msg) for msg in conversation_history
                ] + inputs

        # Prepare the user query (last message in inputs)
        if not inputs:
            raise ValueError("No input messages provided to agent")

        # Get the last user message as the query
        user_msg = inputs[-1] if inputs else None
        chat_hist = inputs[:-1] if len(inputs) > 1 else []

        # Execute agent (ReActAgent.run returns a WorkflowHandler)
        handler = self._agent.run(
            user_msg=user_msg,
            chat_history=chat_hist,
        )

        # Stream or await the result
        agent_response = await self._execute_handler(handler, message)

        # Store result in memory if configured
        if self.step.memory:
            memory = to_memory(session_id, self.step.memory)
            # Convert agent response to chat message
            assistant_message = ChatMessage(
                role=MessageRole.assistant,
                blocks=[
                    ChatContent(
                        type=PrimitiveTypeEnum.text, content=agent_response
                    )
                ],
            )
            memory.put(to_chat_message(assistant_message))

        # Convert result to ChatMessage
        result_value = ChatMessage(
            role=MessageRole.assistant,
            blocks=[
                ChatContent(
                    type=PrimitiveTypeEnum.text, content=agent_response
                )
            ],
        )

        return message.copy_with_variables({output_variable_id: result_value})

    async def _process_completion(
        self,
        message: FlowMessage,
        output_variable_id: str,
    ) -> FlowMessage:
        """Process a completion-based agent request.

        Args:
            message: The FlowMessage to process.
            output_variable_id: The ID of the output variable.

        Returns:
            FlowMessage with the agent completion response.
        """
        # Get input value (expecting text)
        input_value = message.variables.get(self.step.inputs[0].id)
        if not isinstance(input_value, str):
            input_value = str(input_value)

        # Execute agent with the input as a simple message
        handler = self._agent.run(user_msg=input_value)

        # Stream or await the result
        agent_response = await self._execute_handler(handler, message)

        # Return result as text
        return message.copy_with_variables(
            {output_variable_id: agent_response}
        )

    async def _execute_handler(
        self, handler: Any, message: FlowMessage
    ) -> str:
        """Execute the agent handler and return the response.

        Args:
            handler: The WorkflowHandler from ReActAgent.run
            message: The FlowMessage for stream ID generation

        Returns:
            The agent's response as a string
        """
        if self.context.on_stream_event:
            # Generate a unique stream ID for this inference
            stream_id = f"agent-{self.step.id}-{id(message)}"

            async with self.stream_emitter.text_stream(stream_id) as streamer:
                # Stream the agent response
                async for event in handler.stream_events():
                    if hasattr(event, "delta") and event.delta:
                        await streamer.delta(event.delta)

                # Get the final result
                result = await handler
        else:
            # Non-streaming execution
            result = await handler

        return str(result)
