import importlib
import logging
from typing import Any

import requests
from pydantic import BaseModel, ValidationError

from qtype.application.converters.types import PRIMITIVE_TO_PYTHON_TYPE
from qtype.dsl.base_types import PrimitiveTypeEnum
from qtype.interpreter.exceptions import InterpreterError
from qtype.semantic.model import (
    APITool,
    BearerTokenAuthProvider,
    PythonFunctionTool,
    Tool,
    Variable,
)

logger = logging.getLogger(__name__)


def _transform_result_to_variable_type(result: Any, variable: Variable) -> Any:
    """Transform an API result into the expected variable type.

    Args:
        result: The raw result from the API call.
        variable: The variable with type information.

    Returns:
        The transformed result matching the variable's type.

    Raises:
        InterpreterError: If the result cannot be converted to the expected type.
    """
    var_type = variable.type

    # Handle BaseModel subclasses (including custom types)
    if isinstance(var_type, type) and issubclass(var_type, BaseModel):
        try:
            return var_type.model_validate(result)
        except ValidationError as e:
            raise InterpreterError(
                f"Failed to convert API result to {var_type.__name__}: {e}. "
                f"Response body: {result}"
            ) from e

    # Handle primitive types
    elif isinstance(var_type, PrimitiveTypeEnum):
        expected_python_type = PRIMITIVE_TO_PYTHON_TYPE.get(var_type)
        if expected_python_type is None:
            raise InterpreterError(
                f"No Python type mapping found for {var_type}. "
                f"Response body: {result}"
            )

        if not isinstance(result, expected_python_type):
            raise InterpreterError(
                f"Expected {expected_python_type.__name__} for variable '{variable.id}' "
                f"of type {var_type.value}, got {type(result).__name__}. "
                f"Response body: {result}"
            )

        return result

    # Handle other types (fallback)
    else:
        raise InterpreterError(
            f"Unsupported variable type {var_type} for variable '{variable.id}'. "
            f"Response body: {result}"
        )


def _execute_api_tool(tool: APITool, **kwargs) -> dict | Any:
    """Execute an API tool by making an HTTP request.

    Args:
        tool: The API tool to execute.
        **kwargs: Additional keyword arguments passed as inputs.

    Returns:
        The transformed result(s) ready for assignment to output variables.
        Returns a dict if multiple outputs, or the transformed value if single output.

    Raises:
        InterpreterError: If the auth provider is not supported or the request fails.
    """
    # Prepare headers
    headers = tool.headers.copy()

    # Handle authentication
    if tool.auth is not None:
        if isinstance(tool.auth, BearerTokenAuthProvider):
            headers["Authorization"] = f"Bearer {tool.auth.token}"
        else:
            raise InterpreterError(
                f"Unsupported auth provider type: {type(tool.auth).__name__}. "
                "Only BearerTokenAuthProvider is currently supported."
            )

    # Prepare query parameters from tool.parameters and kwargs
    params = {}
    for param in tool.parameters:
        if param.is_set():
            params[param.id] = param.value

    # Add any additional parameters from kwargs
    params.update(kwargs)

    try:
        # Make the HTTP request
        response = requests.request(
            method=tool.method.upper(),
            url=tool.endpoint,
            headers=headers,
            params=params
            if tool.method.upper() in ["GET", "DELETE"]
            else None,
            json=params
            if tool.method.upper() in ["POST", "PUT", "PATCH"]
            else None,
        )

        # Raise an exception for HTTP error status codes
        response.raise_for_status()

        # Return the decoded JSON response
        result = response.json()

        # Transform results based on number of outputs
        if len(tool.outputs) == 1:
            # Single output: transform the entire result
            return _transform_result_to_variable_type(result, tool.outputs[0])
        elif len(tool.outputs) > 1:
            # Multiple outputs: transform each field from the result dict
            if not isinstance(result, dict):
                raise InterpreterError(
                    f"Expected dict result for multiple outputs, got {type(result).__name__}. "
                    f"Response body: {result}"
                )
            transformed_results = {}
            for var in tool.outputs:
                if var.id not in result:
                    raise InterpreterError(
                        f"Output variable '{var.id}' not found in API result. "
                        f"Available keys: {list(result.keys())}. "
                        f"Response body: {result}"
                    )
                transformed_results[var.id] = (
                    _transform_result_to_variable_type(result[var.id], var)
                )
            return transformed_results
        else:
            return None

    except requests.exceptions.RequestException as e:
        raise InterpreterError(f"API request failed: {e}") from e
    except ValueError as e:
        raise InterpreterError(f"Failed to decode JSON response: {e}") from e


def execute(tool: Tool, **kwargs: dict) -> list[Variable]:
    """Execute a tool step.

    Args:
        tool: The tool step to execute.
        **kwargs: Additional keyword arguments.
    """
    logger.debug(f"Executing tool step: {tool.id} with kwargs: {kwargs}")
    # Call the function with the provided arguments
    if any(not inputs.is_set() for inputs in tool.inputs):
        raise InterpreterError(
            f"Tool {tool.id} requires all inputs to be set. Missing inputs: {[var.id for var in tool.inputs if not var.is_set()]}"
        )

    if isinstance(tool, PythonFunctionTool):
        # import the function dynamically
        module = importlib.import_module(tool.module_path)
        function = getattr(module, tool.function_name, None)
        if function is None:
            raise InterpreterError(
                f"Function {tool.function_name} not found in {tool.module_path}"
            )
        inputs = {var.id: var.value for var in tool.inputs if var.is_set()}
        results = function(**inputs)
    elif isinstance(tool, APITool):
        inputs = {var.id: var.value for var in tool.inputs if var.is_set()}
        results = _execute_api_tool(tool, **inputs)
    else:
        raise InterpreterError(f"Unsupported tool type: {type(tool).__name__}")

    # Handle results (same logic for both tool types)
    if isinstance(results, dict) and len(tool.outputs) > 1:
        for var in tool.outputs:
            if var.id in results:
                var.value = results[var.id]
            else:
                raise InterpreterError(
                    f"Output variable {var.id} not found in function results."
                )
    elif len(tool.outputs) == 1:
        tool.outputs[0].value = results
    elif len(tool.outputs) == 0 and results is None:
        pass  # No outputs to assign, and function returned None
    else:
        raise InterpreterError(
            f"The returned value {results} could not be assigned to outputs {[var.id for var in tool.outputs]}."
        )

    return tool.outputs  # type: ignore[return-value]
