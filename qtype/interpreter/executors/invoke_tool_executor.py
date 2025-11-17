from __future__ import annotations

import asyncio
import importlib
import inspect
import logging
import time
import uuid
from typing import Any, AsyncIterator

import requests
from openinference.semconv.trace import OpenInferenceSpanKindValues
from pydantic import BaseModel

from qtype.interpreter.base.base_step_executor import StepExecutor
from qtype.interpreter.base.executor_context import ExecutorContext
from qtype.interpreter.base.stream_emitter import StreamEmitter
from qtype.interpreter.types import FlowMessage
from qtype.semantic.model import (
    APITool,
    BearerTokenAuthProvider,
    InvokeTool,
    PythonFunctionTool,
    Step,
)

logger = logging.getLogger(__name__)

# HTTP methods that require request body instead of query parameters
HTTP_BODY_METHODS = frozenset(["POST", "PUT", "PATCH"])


class ToolExecutionMixin:
    """Mixin providing tool execution capabilities for Python and API tools.

    This mixin can be used by any executor that needs to invoke tools,
    allowing code reuse across InvokeToolExecutor and AgentExecutor.
    """

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        # These will be set by the concrete executor classes
        self.stream_emitter: StreamEmitter
        self.step: Step
        self._resolve_secret: (
            Any  # Will be provided by StepExecutor base class
        )

    async def execute_python_tool(
        self,
        tool: PythonFunctionTool,
        inputs: dict[str, Any],
        original_inputs: dict[str, Any] | None = None,
    ) -> Any:
        """Execute a Python function tool with proper streaming events.

        Args:
            tool: The Python function tool to execute.
            inputs: Dictionary of input parameter names to values
                (may contain parsed Python objects like datetime).
            original_inputs: Optional dictionary of original JSON-serializable
                inputs for streaming events. If not provided, uses inputs.

        Returns:
            The result from the function call.

        Raises:
            ValueError: If the function cannot be found or executed.
        """
        tool_call_id = str(uuid.uuid4())

        # Use original inputs for streaming events if provided
        stream_inputs = original_inputs if original_inputs else inputs

        async with self.stream_emitter.tool_execution(
            tool_call_id=tool_call_id,
            tool_name=tool.function_name,
            tool_input=stream_inputs,
        ) as tool_ctx:
            try:
                module = importlib.import_module(tool.module_path)
                function = getattr(module, tool.function_name, None)
                if function is None:
                    raise ValueError(
                        (
                            f"Function '{tool.function_name}' not found in "
                            f"module '{tool.module_path}'"
                        )
                    )

                if inspect.iscoroutinefunction(function):
                    result = await function(**inputs)
                else:
                    result = await asyncio.to_thread(function, **inputs)
                await tool_ctx.complete(result)
                return result

            except Exception as e:
                error_msg = (
                    f"Failed to execute function {tool.function_name}: {e}"
                )
                logger.error(error_msg, exc_info=True)
                await tool_ctx.error(error_msg)
                raise ValueError(error_msg) from e

    def serialize_value(self, value: Any) -> Any:
        """Recursively serialize values for API requests.

        Args:
            value: The value to serialize.

        Returns:
            Serialized value suitable for JSON encoding.
        """
        if isinstance(value, dict):
            return {k: self.serialize_value(v) for k, v in value.items()}
        elif isinstance(value, list):
            return [self.serialize_value(item) for item in value]
        elif isinstance(value, BaseModel):
            return value.model_dump()
        return value

    async def execute_api_tool(
        self,
        tool: APITool,
        inputs: dict[str, Any],
        original_inputs: dict[str, Any] | None = None,
    ) -> Any:
        """Execute an API tool by making an HTTP request with proper streaming events.

        Args:
            tool: The API tool to execute.
            inputs: Dictionary of input parameter names to values
                (may contain parsed Python objects like datetime).
            original_inputs: Optional dictionary of original JSON-serializable
                inputs for streaming events. If not provided, uses inputs.

        Returns:
            The result from the API call.

        Raises:
            ValueError: If authentication fails or the request fails.
        """
        tool_call_id = str(uuid.uuid4())

        # Use original inputs for streaming events if provided
        stream_inputs = original_inputs if original_inputs else inputs

        async with self.stream_emitter.tool_execution(
            tool_call_id=tool_call_id,
            tool_name=f"{tool.method} {tool.endpoint}",
            tool_input=stream_inputs,
        ) as tool_ctx:
            try:
                # Prepare headers - resolve any SecretReferences
                # Note: ToolExecutionMixin users inherit from StepExecutor
                # which provides _secret_manager
                secret_manager = getattr(self, "_secret_manager")
                context = f"tool '{tool.id}'"
                headers = (
                    secret_manager.resolve_secrets_in_dict(
                        tool.headers, context
                    )
                    if tool.headers
                    else {}
                )

                # Handle authentication
                if tool.auth:
                    if isinstance(tool.auth, BearerTokenAuthProvider):
                        token = self._resolve_secret(tool.auth.token)
                        headers["Authorization"] = f"Bearer {token}"
                    else:
                        raise ValueError(
                            (
                                f"Unsupported auth provider: {type(tool.auth).__name__}"
                            )
                        )

                # Serialize inputs for JSON
                body = self.serialize_value(inputs)

                # Determine if we're sending body or query params
                is_body_method = tool.method.upper() in HTTP_BODY_METHODS

                start_time = time.time()

                response = requests.request(
                    method=tool.method.upper(),
                    url=tool.endpoint,
                    headers=headers,
                    params=None if is_body_method else inputs,
                    json=body if is_body_method else None,
                )

                duration = time.time() - start_time

                # Raise for HTTP errors
                response.raise_for_status()

                logger.debug(
                    f"Request completed in {duration:.2f}s with status "
                    f"{response.status_code}"
                )

                result = response.json()
                await tool_ctx.complete(result)
                return result

            except requests.exceptions.RequestException as e:
                error_msg = f"API request failed: {e}"
                await tool_ctx.error(error_msg)
                raise ValueError(error_msg) from e
            except ValueError as e:
                error_msg = f"Failed to decode JSON response: {e}"
                await tool_ctx.error(error_msg)
                raise ValueError(error_msg) from e


class InvokeToolExecutor(StepExecutor, ToolExecutionMixin):
    """Executor for InvokeTool steps."""

    # Tool invocations should be marked as TOOL type
    span_kind = OpenInferenceSpanKindValues.TOOL

    def __init__(
        self, step: InvokeTool, context: ExecutorContext, **dependencies: Any
    ) -> None:
        super().__init__(step, context, **dependencies)
        if not isinstance(step, InvokeTool):
            raise ValueError(
                "InvokeToolExecutor can only execute InvokeTool steps."
            )
        self.step: InvokeTool = step

    def _prepare_tool_inputs(self, message: FlowMessage) -> dict[str, Any]:
        """Prepare tool inputs from message variables using input bindings.

        Args:
            message: The FlowMessage containing input variables.

        Returns:
            Dictionary mapping tool parameter names to values.

        Raises:
            ValueError: If required inputs are missing.
        """
        tool_inputs = {}

        for tool_param_name, step_var_id in self.step.input_bindings.items():
            # Get tool parameter definition
            tool_param = self.step.tool.inputs.get(tool_param_name)
            if not tool_param:
                raise ValueError(
                    f"Tool parameter '{tool_param_name}' not defined in tool"
                )

            # Get value from message variables
            value = message.variables.get(step_var_id)

            # Handle missing values
            if value is None:
                if not tool_param.optional:
                    raise ValueError(
                        (
                            f"Required input '{step_var_id}' for tool "
                            f"parameter '{tool_param_name}' is missing"
                        )
                    )
                # Skip optional parameters that are missing
                continue

            tool_inputs[tool_param_name] = value

        return tool_inputs

    def _extract_tool_outputs(self, result: Any) -> dict[str, Any]:
        """Extract output variables from tool result using output bindings.

        Args:
            result: The result from tool execution.

        Returns:
            Dictionary mapping step variable IDs to their values.

        Raises:
            ValueError: If required outputs are missing from result.
        """
        output_vars = {}

        for tool_param_name, step_var_id in self.step.output_bindings.items():
            # Get tool parameter definition
            tool_param = self.step.tool.outputs.get(tool_param_name)
            if not tool_param:
                raise ValueError(
                    f"Tool parameter '{tool_param_name}' not defined in tool"
                )

            # Extract value from result
            if isinstance(result, dict):
                value = result.get(tool_param_name)
                if value is None and not tool_param.optional:
                    raise ValueError(
                        (
                            f"Required output '{tool_param_name}' not found "
                            f"in result. Available: {list(result.keys())}"
                        )
                    )
            else:
                # Single output case - use entire result
                value = result

            if value is not None:
                output_vars[step_var_id] = value

        return output_vars

    async def process_message(
        self,
        message: FlowMessage,
    ) -> AsyncIterator[FlowMessage]:
        """Process a single FlowMessage for the InvokeTool step.

        Args:
            message: The FlowMessage to process.
        Yields:
            FlowMessage with tool execution results.
        """
        try:
            # Prepare tool inputs from message variables
            tool_inputs = self._prepare_tool_inputs(message)

            # Execute the tool with proper tool execution context
            # Dispatch to appropriate execution method based on tool type
            if isinstance(self.step.tool, PythonFunctionTool):
                result = await self.execute_python_tool(
                    self.step.tool, tool_inputs
                )
            elif isinstance(self.step.tool, APITool):
                result = await self.execute_api_tool(
                    self.step.tool, tool_inputs
                )
            else:
                raise ValueError(
                    f"Unsupported tool type: {type(self.step.tool).__name__}"
                )

            # Extract outputs from result
            output_vars = self._extract_tool_outputs(result)

            # Yield the result
            yield message.copy_with_variables(output_vars)

        except Exception as e:
            # Emit error event to stream so frontend can display it
            await self.stream_emitter.error(str(e))
            message.set_error(self.step.id, e)
            yield message
