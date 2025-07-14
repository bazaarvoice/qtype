import argparse
import inspect
from pathlib import Path
from typing import Any, Union, get_origin, get_args

import qtype.dsl.model as dsl

TYPES_TO_IGNORE = {
    "Document",
    "StrictBaseModel",
    "VariableTypeEnum",
    "DecoderFormat",
    "VariableTypeEnum",
    "VariableType",
    "DecoderFormat",
}

FIELDS_TO_IGNORE = {"Application.references"}


def generate_semantic_model(args: argparse.Namespace) -> None:
    """Generate semantic model classes from DSL model classes.

    This function inspects the DSL model classes and generates corresponding
    semantic model classes where string ID references are replaced with actual
    object references.
    """
    output_path = Path(args.output)

    # Get all classes from the DSL model module
    dsl_classes = []
    for name, cls in inspect.getmembers(dsl, inspect.isclass):
        if (
            cls.__module__ == dsl.__name__
            and not name.startswith("_")
            and name not in TYPES_TO_IGNORE
            and not name.endswith("List")
        ):
            dsl_classes.append((name, cls))

    # Generate semantic classes
    semantic_classes = []

    for class_name, cls in dsl_classes:
        semantic_code = generate_semantic_class(class_name, cls)
        if semantic_code:
            semantic_classes.append(semantic_code)

    # Generate union types
    union_types = generate_union_types()

    # Write to output file
    with open(output_path, "w") as f:
        # Write header
        f.write('"""\n')
        f.write("Semantic Intermediate Representation models.\n\n")
        f.write(
            "This module contains the semantic models that represent a resolved QType\n"
        )
        f.write(
            "specification where all ID references have been replaced with actual object\n"
        )
        f.write("references.\n\n")
        f.write(
            "Generated automatically with command:\nqtype generate semantic-model\n"
        )
        f.write('"""\n\n')

        # Write imports
        f.write("from __future__ import annotations\n\n")
        f.write("from typing import Any\n\n")
        f.write("from pydantic import BaseModel, Field\n\n")
        f.write("# Import enums and type aliases from DSL\n")
        f.write(
            "from qtype.dsl.model import VariableTypeEnum, DecoderFormat\n\n"
        )

        # Write classes
        f.write("\n\n".join(semantic_classes))
        f.write("\n\n")

        # Write union types
        f.write(union_types)


def generate_semantic_class(class_name: str, cls: type) -> str:
    """Generate a semantic class from a DSL class."""
    semantic_name = f"Semantic{class_name}"

    # Get class docstring
    docstring = cls.__doc__ or f"Semantic version of {class_name}."

    # Determine inheritance
    inheritance = "BaseModel"
    if inspect.isabstract(cls):
        inheritance = "ABC, BaseModel"

    # Check if this class inherits from another DSL class
    for base in cls.__bases__:
        if (
            hasattr(base, "__module__")
            and base.__module__ == dsl.__name__
            and base.__name__ not in TYPES_TO_IGNORE
            and not base.__name__.startswith("_")
        ):
            # This class inherits from another DSL class
            semantic_base = f"Semantic{base.__name__}"
            if inspect.isabstract(cls):
                inheritance = f"ABC, {semantic_base}"
            else:
                inheritance = semantic_base
            break

    # Get field information from the class - only fields defined on this class, not inherited
    fields = []
    if hasattr(cls, "__annotations__") and hasattr(cls, "model_fields"):
        # Only process fields that are actually defined on this class
        for field_name in cls.__annotations__:
            if (
                field_name in cls.model_fields
                and f"{class_name}.{field_name}" not in FIELDS_TO_IGNORE
            ):
                field_info = cls.model_fields[field_name]
                field_type = field_info.annotation
                field_default = field_info.default
                field_description = getattr(field_info, "description", None)

                # Transform the field type
                semantic_type = transform_field_type(field_type, field_name)

                # Check if we should change the default of `None` to `[]` if the type is a list
                if field_default is None and semantic_type.startswith("list["):
                    field_default = []

                # Check if we should change the default of `None` to `{}` if the type is a dict
                if field_default is None and semantic_type.startswith("dict["):
                    field_default = {}

                # Create field definition
                field_def = create_field_definition(
                    field_name, semantic_type, field_default, field_description
                )
                fields.append(field_def)

    # Build class definition
    lines = [f"class {semantic_name}({inheritance}):"]
    lines.append(f'    """{docstring}"""')
    lines.append("")

    # Add config if it's a StrictBaseModel
    if (
        hasattr(cls, "model_config")
        and hasattr(cls.model_config, "extra")
        and cls.model_config.extra == "forbid"
    ):
        lines.append('    model_config = ConfigDict(extra="forbid")')
        lines.append("")

    # Add fields
    if fields:
        lines.extend(fields)
    else:
        lines.append("    pass")

    return "\n".join(lines)


def _is_dsl_type(type_obj: Any) -> bool:
    """Check if a type is a DSL type that should be converted to semantic."""
    if not hasattr(type_obj, "__name__"):
        return False

    # Check if it's defined in the DSL module
    return (
        hasattr(type_obj, "__module__")
        and type_obj.__module__ == dsl.__name__
        and not type_obj.__name__.startswith("_")
    )


def transform_field_type(field_type: Any, field_name: str) -> str:
    """Transform a DSL field type to a semantic field type."""

    # Handle ForwardRef objects
    if hasattr(field_type, "__forward_arg__"):
        # Extract the string from ForwardRef and process it
        forward_ref_str = field_type.__forward_arg__
        actual_type = eval(forward_ref_str, dict(vars(dsl)))
        return transform_field_type(actual_type, field_name)

    # Handle Union types (including | syntax)
    origin = get_origin(field_type)
    args = get_args(field_type)

    if origin is Union or (
        hasattr(field_type, "__class__")
        and field_type.__class__.__name__ == "UnionType"
    ):
        return transform_union_type(args, field_name)

    # Handle list types
    if origin is list:
        if args:
            inner_type = transform_field_type(args[0], field_name)
            return f"list[{inner_type}]"
        return "list"

    # Handle dict types
    if origin is dict:
        if len(args) == 2:
            key_type = transform_field_type(args[0], field_name)
            value_type = transform_field_type(args[1], field_name)
            return f"dict[{key_type}, {value_type}]"
        return "dict"

    # Handle basic types
    if hasattr(field_type, "__name__"):
        type_name = field_type.__name__
        if _is_dsl_type(field_type) and type_name not in TYPES_TO_IGNORE:
            return f"Semantic{type_name}"
        if type_name == "NoneType":
            return "None"
        return type_name

    return str(field_type)


def transform_union_type(args: tuple, field_name: str) -> str:
    """Transform Union types, handling string ID references."""
    # Handle the case where we have a list | None, which in the dsl is needed, but here we will just have an empty list.
    if len(args) == 2:
        list_elems = [
            arg for arg in args if get_origin(arg) in set([list, dict])
        ]
        has_none = any(arg is type(None) for arg in args)
        if len(list_elems) > 0 and has_none:
            # If we have a list and None, we return the list type
            # This is to handle cases like List[SomeType] | None
            # which in the DSL is needed, but here we will just have an empty list.
            return transform_field_type(list_elems[0], field_name)

    # If the union contains a DSL type and a str, we need to drop the str
    if any(_is_dsl_type(arg) for arg in args) and any(
        arg is str for arg in args
    ):
        # There is a DSL type and a str, which indicates something that can reference an ID.
        # drop the str
        args = tuple(arg for arg in args if arg is not str)

    return " | ".join(transform_field_type(a, field_name) for a in args)


def create_field_definition(
    field_name: str,
    field_type: str,
    field_default: Any,
    field_description: str | None,
) -> str:
    """Create a field definition string."""
    # Handle aliases
    alias_part = ""
    if field_name == "else_":
        alias_part = ', alias="else"'

    # Handle default values
    # Check for PydanticUndefined (required field)
    from pydantic_core import PydanticUndefined

    if field_default is PydanticUndefined or field_default is ...:
        default_part = "..."
    elif field_default is None:
        default_part = "None"
    elif isinstance(field_default, str):
        default_part = f'"{field_default}"'
    elif hasattr(field_default, "__name__"):  # Enum or callable
        # Handle enum defaults properly
        if hasattr(field_default, "__module__") and hasattr(
            field_default, "__qualname__"
        ):
            # For enums like DecoderFormat.json, use the qualified name
            default_part = f"{field_default.__qualname__}"
        else:
            default_part = str(field_default)
    else:
        default_part = str(field_default)

    # Create Field definition
    field_parts = [default_part]
    if field_description:
        # Escape quotes and handle multiline descriptions
        escaped_desc = field_description.replace('"', '\\"').replace(
            "\n", "\\n"
        )
        field_parts.append(f'description="{escaped_desc}"')
    if alias_part:
        field_parts.append(alias_part.lstrip(", "))

    field_def = f"Field({', '.join(field_parts)})"

    return f"    {field_name}: {field_type} = {field_def}"


def generate_union_types() -> str:
    """Generate union type definitions."""
    return """# Union types for semantic models
SemanticToolType = SemanticAPITool | SemanticPythonFunctionTool

SemanticStepType = (
    SemanticAgent |
    SemanticAPITool |
    SemanticCondition |
    SemanticDecoder |
    SemanticDocumentSearch |
    SemanticFlow |
    SemanticLLMInference |
    SemanticPromptTemplate |
    SemanticPythonFunctionTool |
    SemanticVectorSearch
)

SemanticIndexType = SemanticDocumentIndex | SemanticVectorIndex

SemanticModelType = SemanticEmbeddingModel | SemanticModel
"""
