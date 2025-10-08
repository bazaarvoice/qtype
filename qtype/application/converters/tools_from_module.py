import importlib
import inspect
from typing import Any, Type, Union, get_args, get_origin

from pydantic import BaseModel

from qtype.application.converters.types import PYTHON_TYPE_TO_PRIMITIVE_TYPE
from qtype.base.types import PrimitiveTypeEnum
from qtype.dsl.model import (
    CustomType,
    ListType,
    PythonFunctionTool,
    ToolParameter,
    VariableType,
)


def tools_from_module(
    module_path: str,
) -> tuple[list[PythonFunctionTool], list[CustomType]]:
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

        custom_types: dict[str, CustomType] = {}

        # Create Tool instances from functions
        tools = [
            _create_tool_from_function(func_name, func_info, custom_types)
            for func_name, func_info in functions.items()
        ]
        return (tools, list(custom_types.values()))
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
    func_name: str,
    func_info: dict[str, Any],
    custom_types: dict[str, CustomType],
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

    # Create input parameters from function parameters
    inputs = {
        p["name"]: ToolParameter(
            type=_map_python_type_to_variable_type(p["type"], custom_types),
            optional=p["default"] != inspect.Parameter.empty,
        )
        for p in func_info["parameters"]
    }

    # Create output parameter based on return type
    tool_id = func_info["module"] + "." + func_name

    output_type = _map_python_type_to_variable_type(
        func_info["return_type"], custom_types
    )

    outputs = {"result": ToolParameter(type=output_type, optional=False)}

    return PythonFunctionTool(
        id=tool_id,
        name=func_name,
        module_path=func_info["module"],
        function_name=func_name,
        description=description,
        inputs=inputs,
        outputs=outputs,
    )


def _pydantic_to_custom_types(
    model_cls: Type[BaseModel],
    custom_types: dict[str, CustomType],
) -> str:
    """
    Converts a Pydantic BaseModel class into a QType CustomType.
    This function extracts the model's fields and their types, converting them
    into a CustomType definition.

    If multiple nested types are found, they are recursively converted
    into CustomType definitions.

    Args:
        model_cls: The Pydantic model class to convert.

    Returns:
        A dictionary mapping field names to their corresponding CustomType definitions.
    """
    properties = {}
    model_name = model_cls.__name__
    if model_name in custom_types:
        return model_name  # Already processed

    for field_name, field_info in model_cls.model_fields.items():
        # Use the annotation (the type hint) for the field
        field_type = field_info.annotation
        if field_type is None:
            raise TypeError(
                f"Field '{field_name}' in '{model_name}' must have a type hint."
            )
        elif get_origin(field_type) is Union:
            # Assume the union means it's optional
            field_type = [
                t for t in get_args(field_type) if t is not type(None)
            ][0]
            rv = _map_python_type_to_type_str(field_type, custom_types)
            properties[field_name] = f"{rv}?"
        elif get_origin(field_type) is list:
            inner_type = get_args(field_type)[0]
            rv = _map_python_type_to_type_str(inner_type, custom_types)
            properties[field_name] = f"list[{rv}]"
        else:
            properties[field_name] = _map_python_type_to_type_str(
                field_type, custom_types
            )

    # Add the custom type to the list
    custom_types[model_name] = CustomType(
        id=model_name,
        properties=properties,
        description=model_cls.__doc__ or f"Custom type for {model_name}",
    )
    return model_name


def _map_python_type_to_variable_type(
    python_type: Any,
    custom_types: dict[str, CustomType],
) -> str | VariableType:
    """
    Map Python type annotations to QType VariableType.

    Args:
        python_type: Python type annotation.

    Returns:
        VariableType compatible value.
    """

    # Check for generic types like list[str], list[int], etc.
    origin = get_origin(python_type)
    if origin is list:
        # Handle list[T] annotations
        args = get_args(python_type)
        if len(args) == 1:
            element_type_annotation = args[0]
            # Recursively map the element type
            element_type = _map_python_type_to_variable_type(
                element_type_annotation, custom_types
            )
            # Support lists of both primitive types and custom types
            if isinstance(element_type, PrimitiveTypeEnum):
                return ListType(element_type=element_type)
            elif isinstance(element_type, str):
                # Custom type reference
                return ListType(element_type=element_type)
            else:
                raise ValueError(
                    f"List element type must be primitive or custom type, got: {element_type}"
                )
        else:
            raise ValueError(
                f"List type must have exactly one type argument, got: {args}"
            )

    if python_type in PYTHON_TYPE_TO_PRIMITIVE_TYPE:
        return PYTHON_TYPE_TO_PRIMITIVE_TYPE[python_type]
    elif python_type in get_args(VariableType):
        # If it's a domain type, return its name
        return python_type  # type: ignore[no-any-return]
    elif inspect.isclass(python_type) and issubclass(python_type, BaseModel):
        # If it's a Pydantic model, create or retrieve its CustomType definition
        return _pydantic_to_custom_types(python_type, custom_types)
    raise ValueError(
        f"Unsupported Python type '{python_type}' for VariableType mapping"
    )


def _map_python_type_to_type_str(
    python_type: Any,
    custom_types: dict[str, CustomType],
) -> str:
    var_type = _map_python_type_to_variable_type(python_type, custom_types)
    if isinstance(var_type, PrimitiveTypeEnum):
        return var_type.value
    elif inspect.isclass(python_type):
        return python_type.__name__
    else:
        return str(python_type)
