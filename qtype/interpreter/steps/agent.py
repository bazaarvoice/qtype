import asyncio
import importlib
import logging
from typing import Any

from llama_index.core.agent.workflow import ReActAgent
from llama_index.core.base.llms.types import ChatMessage as LlamaChatMessage
from llama_index.core.tools import AsyncBaseTool, FunctionTool
from llama_index.core.workflow import Context
from llama_index.core.workflow.handler import WorkflowHandler  # type: ignore

from qtype.dsl.domain_types import ChatMessage
from qtype.interpreter.conversions import (
    from_chat_message,
    to_chat_message,
    to_llm,
    to_memory,
)
from qtype.interpreter.exceptions import InterpreterError
from qtype.semantic.model import Agent, APITool, PythonFunctionTool, Variable

logger = logging.getLogger(__name__)


def to_llama_tool(tool: PythonFunctionTool) -> AsyncBaseTool:
    """Convert a qtype Tool to a LlamaIndex Tool."""
    # We want to get the function named by the tool -- get ".tools.<tool_name>"
    # This assumes the tool name matches a function in the .tools module
    module = importlib.import_module(tool.module_path)
    function = getattr(module, tool.function_name, None)
    if function is None:
        raise ValueError(
            f"Tool function '{tool.function_name}' not found in module '{tool.module_path}'."
        )

    return FunctionTool.from_defaults(
        fn=function, name=tool.name, description=tool.description
    )


def execute(agent: Agent, **kwargs: dict[str, Any]) -> list[Variable]:
    """Execute an agent step.

    Args:
        agent: The agent step to execute.
        **kwargs: Additional keyword arguments.
    """
    logger.debug(f"Executing agent step: {agent.id}")
    if len(agent.outputs) != 1:
        raise InterpreterError(
            "LLMInference step must have exactly one output variable."
        )
    output_variable = agent.outputs[0]

    # prepare the input for the agent
    if len(agent.inputs) != 1:
        # TODO: Support multiple inputs by shoving it into the chat history?
        raise InterpreterError(
            "Agent step must have exactly one input variable."
        )

    input_variable = agent.inputs[0]
    if input_variable.type == ChatMessage:
        input: LlamaChatMessage | str = to_chat_message(input_variable.value)  # type: ignore
    else:
        input: LlamaChatMessage | str = input_variable.value  # type: ignore

    # Pepare the tools
    # TODO: support api tools
    if any(isinstance(tool, APITool) for tool in agent.tools):
        raise NotImplementedError(
            "APITool is not supported in the current implementation. Please use PythonFunctionTool."
        )
    tools = [
        to_llama_tool(tool)  # type: ignore
        for tool in (agent.tools if agent.tools else [])
    ]

    # prep memory
    # Note to_memory is a cached resource so this will get existing memory if available
    memory = (
        to_memory(kwargs.get("session_id"), agent.memory)
        if agent.memory
        else None
    )

    # Run the agent
    async def run_agent() -> WorkflowHandler:
        logger.debug(
            f"Starting agent '{agent.id}' execution with input length: {len(str(input))} (ReAct mode)"
        )
        re_agent = ReActAgent(
            name=agent.id,
            tools=tools,  # type: ignore
            system_prompt=agent.system_message,
            llm=to_llm(agent.model, agent.system_message),  # type: ignore
        )
        ctx = Context(re_agent)  # type: ignore
        # TODO: implement checkpoint_callback to call stream_fn?
        handler = re_agent.run(input, chat_memory=memory, ctx=ctx)
        result = await handler
        logger.debug(
            f"Agent '{agent.id}' execution completed successfully (ReAct mode)"
        )
        return result

    result = asyncio.run(run_agent())

    if output_variable.type == ChatMessage:
        output_variable.value = from_chat_message(result.response)  # type: ignore
    else:
        output_variable.value = result.response.content  # type: ignore

    return agent.outputs
