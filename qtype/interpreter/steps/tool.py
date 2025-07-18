import importlib
import logging

from qtype.interpreter.exceptions import InterpreterError
from qtype.semantic.model import PythonFunctionTool, Tool, Variable

logger = logging.getLogger(__name__)


def execute(tool: Tool, **kwargs: dict) -> list[Variable]:
    """Execute a tool step.

    Args:
        tool: The tool step to execute.
        **kwargs: Additional keyword arguments.
    """
    logger.debug(f"Executing tool step: {tool.id} with kwargs: {kwargs}")

    if isinstance(tool, PythonFunctionTool):
        # import the function dynamically
        module = importlib.import_module(tool.module_path)
        function = getattr(module, tool.function_name, None)
        if function is None:
            raise InterpreterError(
                f"Function {tool.function_name} not found in {tool.module_path}"
            )
        # Call the function with the provided arguments
        if any(not inputs.is_set() for inputs in tool.inputs):
            raise InterpreterError(
                f"Tool {tool.id} requires all inputs to be set. Missing inputs: {[var.id for var in tool.inputs if not var.is_set()]}"
            )
        inputs = {var.id: var.value for var in tool.inputs if var.is_set()}
        results = function(**inputs)
    else:
        # TODO: support api tools
        raise InterpreterError(f"Unsupported tool type: {type(tool).__name__}")

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
    else:
        raise InterpreterError(
            f"The returned value {results} could not be assigned to outputs {[var.id for var in tool.outputs]}."
        )

    return tool.outputs  # type: ignore[return-value]
