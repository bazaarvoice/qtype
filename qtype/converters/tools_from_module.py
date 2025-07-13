import importlib
import inspect
from typing import Any

from qtype.dsl.model import (
    PythonFunctionTool,
    Variable,
    VariableType,
)


from qtype.util import TYPE_TO_VARIABLE


def tools_from_module(
    module_path: str,
) -> list[PythonFunctionTool]:
    """
    Load tools from a Python module by introspecting its functions.

    Args:
        provider: The PythonModuleToolProvider instance containing module_path.

    Returns:
        List of Tool instances created from module functions.

    Raises:
        ImportError: If the module cannot be imported.
        ValueError: If no valid functions are found in the module.
    """
    try:
        # Import the module
        module = importlib.import_module(module_path)

        # Get all functions from the module
        functions = _get_module_functions(module_path, module)

        if not functions:
            raise ValueError(
                f"No public functions found in module '{module_path}'"
            )

        # Create Tool instances from functions
        return [
            _create_tool_from_function(func_name, func_info)
            for func_name, func_info in functions.items()
        ]
    except ImportError as e:
        raise ImportError(f"Cannot import module '{module_path}': {e}") from e


def _get_module_functions(
    module_path: str, module: Any
) -> dict[str, dict[str, Any]]:
    """
    Extract all public functions from a module with their metadata.

    Args:
        module_path: Dot-separated module path for reference.
        module: The imported module object.

    Returns:
        Dictionary mapping function names to their metadata.
    """
    functions = {}

    for name, obj in inspect.getmembers(module, inspect.isfunction):
        # Skip private functions (starting with _)
        if name.startswith("_"):
            continue

        # Only include functions defined in this module
        if obj.__module__ != module_path:
            continue

        # Get function signature
        sig = inspect.signature(obj)

        # Extract parameter information
        parameters = []
        for param_name, param in sig.parameters.items():
            param_info = {
                "name": param_name,
                "type": param.annotation,
                "default": param.default,
                "kind": param.kind,
            }
            parameters.append(param_info)

        # Get return type
        if sig.return_annotation == inspect.Signature.empty:
            raise ValueError(
                f"Function '{name}' in module '{module_path}' must have a return type annotation"
            )

        return_type = sig.return_annotation

        functions[name] = {
            "callable": obj,
            "signature": sig,
            "docstring": inspect.getdoc(obj) or "",
            "parameters": parameters,
            "return_type": return_type,
            "module": module_path,
        }

    return functions


def _create_tool_from_function(
    func_name: str, func_info: dict[str, Any]
) -> PythonFunctionTool:
    """
    Convert function metadata into a Tool instance.

    Args:
        func_name: Name of the function.
        func_info: Function metadata from _get_module_functions.

    Returns:
        Tool instance configured from the function.
    """
    # Parse docstring to extract description
    description = (
        func_info["docstring"].split("\n")[0]
        if func_info["docstring"]
        else f"Function {func_name}"
    )

    # Create input variables from function parameters
    input_variables = [
        Variable(
            id=p["name"],
            type=_map_python_type_to_variable_type(p["type"]),
        )
        for p in func_info["parameters"]
    ]

    # Create output variable based on return type
    output_type = _map_python_type_to_variable_type(func_info["return_type"])

    tool_id = func_info["module"] + "." + func_name
    output_variable = Variable(
        id=f"{tool_id}.result",
        type=output_type,
    )

    return PythonFunctionTool(
        id=tool_id,
        name=func_name,
        module_path=func_info["module"],
        function_name=func_name,
        description=description,
        inputs=input_variables if len(input_variables) > 0 else None,  # type: ignore
        outputs=[output_variable],
    )


def _map_python_type_to_variable_type(
    python_type: type | None,
) -> VariableType:
    """
    Map Python type annotations to QType VariableType.

    Args:
        python_type: Python type annotation.

    Returns:
        VariableType compatible value.
    """

    if python_type is not None:
        if python_type in TYPE_TO_VARIABLE:
            return TYPE_TO_VARIABLE[python_type]
        else:
            # If the type is a Pydantic model, use its model_dump method
            # to convert it to a dictionary representation
            try:
                schema = python_type.model_json_schema()  # type: ignore
                return {n: p["type"] for n, p in schema["properties"].items()}
            except AttributeError:
                pass
    raise ValueError(
        f"Unsupported Python type '{python_type}' for VariableType mapping"
    )
