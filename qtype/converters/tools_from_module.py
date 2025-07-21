import importlib
import inspect
from datetime import date, datetime, time
from typing import Any, Type, Union, get_args, get_origin

from pydantic import BaseModel

from qtype.dsl.model import (
    ArrayTypeDefinition,
    ObjectTypeDefinition,
    PrimitiveTypeEnum,
    PythonFunctionTool,
    Variable,
    VariableType,
)

VARIABLE_TO_TYPE = {
    # VariableTypeEnum.audio: bytes, # TODO: Define a proper audio type
    PrimitiveTypeEnum.boolean: bool,  # No boolean type in enum, using Python's
    PrimitiveTypeEnum.bytes: bytes,
    PrimitiveTypeEnum.date: date,
    PrimitiveTypeEnum.datetime: datetime,
    PrimitiveTypeEnum.int: int,
    # VariableTypeEnum.file: bytes,  # TODO: Define a proper file type
    # VariableTypeEnum.image: bytes,  # TODO: Define a proper image type
    PrimitiveTypeEnum.float: float,
    PrimitiveTypeEnum.text: str,
    PrimitiveTypeEnum.time: time,
    # VariableTypeEnum.video: bytes,  # TODO: Define a proper video type
}

TYPE_TO_VARIABLE = {v: k for k, v in VARIABLE_TO_TYPE.items()}

assert len(VARIABLE_TO_TYPE) == len(
    TYPE_TO_VARIABLE
), "Variable to type mapping is not one-to-one"


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
    tool_id = func_info["module"] + "." + func_name

    output_type = _map_python_type_to_variable_type(func_info["return_type"])

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


def _map_type_to_dsl(
    pydantic_type: Type[Any], model_name: str
) -> VariableType | str:
    """
    Recursively maps a Python/Pydantic type to a DSL Type Definition.

    Args:
        pydantic_type: The type hint to map (e.g., str, list[int], MyPydanticModel).
        model_name: The name of the model being processed, for generating unique IDs.

    Returns:
        A PrimitiveTypeEnum member, an ObjectTypeDefinition, an ArrayTypeDefinition,
        or a string reference to another type.
    """
    origin = get_origin(pydantic_type)
    args = get_args(pydantic_type)

    # --- Handle Lists ---
    if origin in (list, list):
        if not args:
            raise TypeError(
                "List types must be parameterized, e.g., list[str]."
            )

        # Recursively map the inner type of the list
        inner_type = _map_type_to_dsl(args[0], model_name)

        # Create a unique ID for this specific array definition
        array_id = (
            f"{model_name}.{getattr(inner_type, 'id', str(inner_type))}_Array"
        )

        return ArrayTypeDefinition(
            id=array_id,
            type=inner_type,
            description=f"An array of {getattr(inner_type, 'id', inner_type)}.",
        )

    # --- Handle Unions (specifically for Optional[T]) ---
    if origin is Union:
        # Filter out NoneType to handle Optional[T]
        non_none_args = [arg for arg in args if arg is not type(None)]
        if len(non_none_args) == 1:
            return _map_type_to_dsl(non_none_args[0], model_name)
        else:
            # For more complex unions, you might decide on a specific handling strategy.
            # For now, we'll raise an error as it's ambiguous.
            raise TypeError(
                "Complex Union types are not supported for automatic conversion."
            )

    # --- Handle Nested Pydantic Models ---
    if inspect.isclass(pydantic_type) and issubclass(pydantic_type, BaseModel):
        # If it's a nested model, recursively call the main function.
        # This returns a full definition for the nested object.
        return pydantic_to_object_definition(pydantic_type)

    # --- Handle Primitive Types ---
    # This could be expanded with more sophisticated mapping.

    if pydantic_type in TYPE_TO_VARIABLE:
        return TYPE_TO_VARIABLE[pydantic_type]

    raise TypeError(f"Unsupported type for DSL conversion: {pydantic_type}")


def pydantic_to_object_definition(
    model_cls: Type[BaseModel],
) -> ObjectTypeDefinition:
    """
    Converts a Pydantic BaseModel class into a QType ObjectTypeDefinition.

    This function introspects the model's fields, recursively converting them
    into the appropriate DSL type definitions (primitive, object, or array).

    Args:
        model_cls: The Pydantic model class to convert.

    Returns:
        An ObjectTypeDefinition representing the Pydantic model.
    """
    properties = {}
    model_name = model_cls.__name__

    for field_name, field_info in model_cls.model_fields.items():
        # Use the annotation (the type hint) for the field
        field_type = field_info.annotation
        if field_type is None:
            raise TypeError(
                f"Field '{field_name}' in '{model_name}' must have a type hint."
            )

        properties[field_name] = _map_type_to_dsl(field_type, model_name)

    return ObjectTypeDefinition(
        id=model_name,
        description=model_cls.__doc__ or f"A definition for {model_name}.",
        properties=properties,
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
                return pydantic_to_object_definition(python_type)
            except AttributeError:
                pass
    raise ValueError(
        f"Unsupported Python type '{python_type}' for VariableType mapping"
    )


VARIABLE_TO_TYPE = {
    # VariableTypeEnum.audio: bytes, # TODO: Define a proper audio type
    PrimitiveTypeEnum.boolean: bool,  # No boolean type in enum, using Python's
    PrimitiveTypeEnum.bytes: bytes,
    PrimitiveTypeEnum.date: date,
    PrimitiveTypeEnum.datetime: datetime,
    PrimitiveTypeEnum.int: int,
    # VariableTypeEnum.file: bytes,  # TODO: Define a proper file type
    # VariableTypeEnum.image: bytes,  # TODO: Define a proper image type
    PrimitiveTypeEnum.float: float,
    PrimitiveTypeEnum.text: str,
    PrimitiveTypeEnum.time: time,
    # VariableTypeEnum.video: bytes,  # TODO: Define a proper video type
}
