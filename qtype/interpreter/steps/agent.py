import asyncio
import importlib
import logging
from typing import Any

from llama_index.core.agent.workflow import ReActAgent
from llama_index.core.tools import AsyncBaseTool, FunctionTool
from llama_index.core.workflow import Context
from llama_index.core.workflow.handler import WorkflowHandler  # type: ignore

from qtype.interpreter.conversions import to_llm
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
    # TODO: support api tools
    if any(isinstance(tool, APITool) for tool in agent.tools):
        raise NotImplementedError(
            "APITool is not supported in the current implementation. Please use PythonFunctionTool."
        )

    tools = [
        to_llama_tool(tool)  # type: ignore
        for tool in (agent.tools if agent.tools else [])
    ]
    # TODO: Add Memory
    # TODO: Add Chat functionality?
    if len(agent.inputs) != 1:
        raise InterpreterError(
            "LLMInference step must have exactly one input variable."
        )
    input = agent.inputs[0].value

    async def run_agent() -> WorkflowHandler:
        logger.info(
            f"Starting agent '{agent.id}' execution with input length: {len(str(input))} (ReAct mode)"
        )
        re_agent = ReActAgent(
            name=agent.id,
            tools=tools,  # type: ignore
            system_prompt=agent.system_message,
            llm=to_llm(agent.model, agent.system_message),  # type: ignore
        )
        ctx = Context(re_agent)  # type: ignore
        handler = re_agent.run(input, ctx=ctx)
        result = await handler
        logger.debug(
            f"Agent '{agent.id}' execution completed successfully (ReAct mode)"
        )
        return result

    result = asyncio.run(run_agent())
    output_variable.value = result.response.content

    return agent.outputs
