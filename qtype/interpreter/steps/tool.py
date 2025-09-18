import importlib
import logging
import time
from typing import Any, Callable

import requests
from pydantic import BaseModel

from qtype.interpreter.exceptions import InterpreterError
from qtype.semantic.model import (
    APITool,
    BearerTokenAuthProvider,
    Invoke,
    PythonFunctionTool,
    Variable,
)

logger = logging.getLogger(__name__)


def _execute_function_tool(
    tool: PythonFunctionTool, inputs: dict[str, Any]
) -> Any:
    """Execute a Python function tool.

    Args:
        tool: The Python function tool to execute.
        inputs: Dictionary of input parameter names to values.

    Returns:
        The result from the function call.

    Raises:
        InterpreterError: If the function cannot be found or executed.
    """
    try:
        module = importlib.import_module(tool.module_path)
        function = getattr(module, tool.function_name, None)
        if function is None:
            raise InterpreterError(
                f"Function {tool.function_name} not found in {tool.module_path}"
            )
        return function(**inputs)
    except Exception as e:
        raise InterpreterError(
            f"Failed to execute function {tool.function_name}: {e}"
        ) from e


def _execute_api_tool(
    tool: APITool, inputs: dict[str, Any], stream_fn: Callable | None = None
) -> Any:
    """Execute an API tool by making an HTTP request.

    Args:
        tool: The API tool to execute.
        inputs: Dictionary of input parameter names to values.

    Returns:
        The result from the API call.

    Raises:
        InterpreterError: If the auth provider is not supported or the request fails.
    """
    # Prepare headers
    headers = tool.headers.copy() if tool.headers else {}

    # Handle authentication
    if tool.auth is not None:
        if isinstance(tool.auth, BearerTokenAuthProvider):
            headers["Authorization"] = f"Bearer {tool.auth.token}"
        else:
            raise InterpreterError(
                f"Unsupported auth provider type: {type(tool.auth).__name__}. "
                "Only BearerTokenAuthProvider is currently supported."
            )

    # Prepare request body
    def dump_if_necessary(value: Any) -> Any:
        # if value is a dictionary, call recursively
        if isinstance(value, dict):
            return {k: dump_if_necessary(v) for k, v in value.items()}
        elif isinstance(value, BaseModel):
            return value.model_dump()
        return value

    # Use inputs for request body
    body = None
    if inputs:
        body = dump_if_necessary(inputs)

    try:
        if stream_fn:
            stream_fn(f"Making request to {tool.endpoint}...")

        logging.info(f"Making request to {tool.endpoint}")
        # Record start time
        start_time = time.time()

        # Make the HTTP request
        response = requests.request(
            method=tool.method.upper(),
            url=tool.endpoint,
            headers=headers,
            params=None
            if tool.method.upper() in ["POST", "PUT", "PATCH"]
            else inputs,
            json=body
            if tool.method.upper() in ["POST", "PUT", "PATCH"]
            else None,
        )

        # Calculate and log request duration
        duration = time.time() - start_time
        if stream_fn:
            stream_fn(
                f"Request to {tool.endpoint} completed in {duration:.2f} seconds"
            )
        logging.info(
            f"Request to {tool.endpoint} completed in {duration:.2f} seconds"
        )

        # Raise an exception for HTTP error status codes
        response.raise_for_status()

        # Return the decoded JSON response
        return response.json()

    except requests.exceptions.RequestException as e:
        raise InterpreterError(f"API request failed: {e}") from e
    except ValueError as e:
        raise InterpreterError(f"Failed to decode JSON response: {e}") from e


def execute(
    step: Invoke, stream_fn: Callable | None = None, **kwargs: dict[str, Any]
) -> list[Variable]:
    """Execute an Invoke step.

    Args:
        step: The Invoke step to execute.
        **kwargs: Additional keyword arguments.

    Returns:
        List of output variables with their values set.
    """
    logger.debug(f"Executing invoke step: {step.id}")

    # Create lookup maps for efficient access
    step_inputs_map = {var.id: var for var in step.inputs}
    step_outputs_map = {var.id: var for var in step.outputs}
    tool_inputs_map = step.tool.inputs or {}
    tool_outputs_map = step.tool.outputs or {}

    # Build inputs dictionary using input bindings
    tool_inputs = {}
    for tool_input_name, step_input_id in step.input_bindings.items():
        # Validate tool parameter exists
        if tool_input_name not in tool_inputs_map:
            raise InterpreterError(
                f"Tool input parameter '{tool_input_name}' not found in tool definition"
            )
        tool_param = tool_inputs_map[tool_input_name]

        if step_input_id in step_inputs_map:
            step_input = step_inputs_map[step_input_id]
            # Check if input is set
            if step_input.is_set():
                tool_inputs[tool_input_name] = step_input.value
            elif not tool_param.optional:
                raise InterpreterError(
                    f"Input '{step_input_id}' is required but not set"
                )
        else:
            logging.warning(
                f"Step input '{step_input_id}' not found in step inputs, using it as literal for {tool_input_name}"
            )
            tool_inputs[tool_input_name] = step_input_id

    # Execute the tool
    if isinstance(step.tool, PythonFunctionTool):
        result = _execute_function_tool(step.tool, tool_inputs)
    elif isinstance(step.tool, APITool):
        result = _execute_api_tool(step.tool, tool_inputs)
    else:
        raise InterpreterError(
            f"Unsupported tool type: {type(step.tool).__name__}"
        )

    # Map results to output variables using output bindings
    for tool_output_name, step_output_id in step.output_bindings.items():
        # Validate step output exists
        if step_output_id not in step_outputs_map:
            raise InterpreterError(
                f"Step output '{step_output_id}' not found in step outputs"
            )
        step_output = step_outputs_map[step_output_id]

        # Validate tool output parameter exists
        if tool_output_name not in tool_outputs_map:
            raise InterpreterError(
                f"Tool output parameter '{tool_output_name}' not found in tool definition"
            )
        tool_output_param = tool_outputs_map[tool_output_name]

        # Extract the value from the result
        if isinstance(result, dict):
            if tool_output_name in result:
                step_output.value = result[tool_output_name]
            elif not tool_output_param.optional:
                raise InterpreterError(
                    f"Tool output '{tool_output_name}' not found in result. "
                    f"Available keys: {list(result.keys())}"
                )
        else:
            # Single output case - use the entire result
            step_output.value = result

    return step.outputs
