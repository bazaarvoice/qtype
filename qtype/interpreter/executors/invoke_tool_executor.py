from __future__ import annotations

import importlib
import logging
import time
from typing import Any, AsyncIterator, cast

import requests
from openinference.semconv.trace import OpenInferenceSpanKindValues
from pydantic import BaseModel

from qtype.interpreter.base.base_step_executor import StepExecutor
from qtype.interpreter.types import FlowMessage
from qtype.semantic.model import (
    APITool,
    BearerTokenAuthProvider,
    InvokeTool,
    PythonFunctionTool,
)

logger = logging.getLogger(__name__)


class ToolExecutionMixin:
    """Mixin providing tool execution capabilities for Python and API tools.

    This mixin can be used by any executor that needs to invoke tools,
    allowing code reuse across InvokeToolExecutor and AgentExecutor.
    """

    async def execute_python_tool(
        self,
        tool: PythonFunctionTool,
        inputs: dict[str, Any],
    ) -> Any:
        """Execute a Python function tool.

        Args:
            tool: The Python function tool to execute.
            inputs: Dictionary of input parameter names to values.

        Returns:
            The result from the function call.

        Raises:
            ValueError: If the function cannot be found or executed.
        """
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

            result = function(**inputs)
            return result

        except Exception as e:
            raise ValueError(
                f"Failed to execute function {tool.function_name}: {e}"
            ) from e

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
    ) -> Any:
        """Execute an API tool by making an HTTP request.

        Args:
            tool: The API tool to execute.
            inputs: Dictionary of input parameter names to values.

        Returns:
            The result from the API call.

        Raises:
            ValueError: If authentication fails or the request fails.
        """
        # Prepare headers
        headers = tool.headers.copy() if tool.headers else {}

        # Handle authentication
        if tool.auth:
            if isinstance(tool.auth, BearerTokenAuthProvider):
                headers["Authorization"] = f"Bearer {tool.auth.token}"
            else:
                raise ValueError(
                    (f"Unsupported auth provider: {type(tool.auth).__name__}")
                )

        # Serialize inputs for JSON
        body = self.serialize_value(inputs) if inputs else None

        # Determine if we're sending body or query params
        is_body_method = tool.method.upper() in ["POST", "PUT", "PATCH"]

        try:
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

            return response.json()

        except requests.exceptions.RequestException as e:
            raise ValueError(f"API request failed: {e}") from e
        except ValueError as e:
            raise ValueError(f"Failed to decode JSON response: {e}") from e


class InvokeToolExecutor(StepExecutor, ToolExecutionMixin):
    """Executor for InvokeTool steps."""

    # Tool invocations should be marked as TOOL type
    span_kind = OpenInferenceSpanKindValues.TOOL

    def __init__(self, step: InvokeTool, **dependencies):
        super().__init__(step, **dependencies)
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

    async def _execute_tool(
        self,
        tool: APITool | PythonFunctionTool,
        inputs: dict[str, Any],
    ) -> Any:
        """Execute a tool and emit status updates.

        Args:
            tool: The tool to execute.
            inputs: Dictionary of input parameter names to values.

        Returns:
            The result from tool execution.
        """
        if isinstance(tool, PythonFunctionTool):
            await self.stream_emitter.status(
                f"Calling Python function: {tool.function_name}"
            )
            result = await self.execute_python_tool(tool, inputs)
            await self.stream_emitter.status(
                f"Function {tool.function_name} completed successfully"
            )
            return result
        elif isinstance(tool, APITool):
            await self.stream_emitter.status(
                f"Making {tool.method} request to {tool.endpoint}"
            )
            return await self.execute_api_tool(tool, inputs)
        else:
            raise ValueError(f"Unsupported tool type: {type(tool).__name__}")

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

            # Execute the tool with status updates
            # Cast is safe because semantic validation ensures only
            # supported tool types
            result = await self._execute_tool(
                cast(APITool | PythonFunctionTool, self.step.tool),
                tool_inputs,
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
