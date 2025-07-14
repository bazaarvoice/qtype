import argparse
import inspect
from pathlib import Path
from typing import Any
import subprocess

import qtype.dsl.model as dsl
import networkx as nx

from qtype.semantic.resolver import (
    TYPES_TO_IGNORE,
)
from qtype.semantic.resolver import dsl_to_semantic_type_name  # Add this dependency for topological sorting

FIELDS_TO_IGNORE = {"Application.references"}


def sort_classes_by_inheritance(
    classes: list[tuple[str, type]],
) -> list[tuple[str, type]]:
    """Sort classes based on their inheritance hierarchy."""
    graph = nx.DiGraph()
    class_dict = dict(classes)

    # Build dependency graph
    for class_name, cls in classes:
        graph.add_node(class_name)
        for base in cls.__bases__:
            if (
                hasattr(base, "__module__")
                and base.__module__ == dsl.__name__
                and base.__name__ not in TYPES_TO_IGNORE
                and not base.__name__.startswith("_")
            ):
                graph.add_edge(base.__name__, class_name)

    sorted_names = list(nx.topological_sort(graph))

    # sorted_names = sorted(graph.nodes, key=lambda node: depths[node])
    return [(name, class_dict[name]) for name in sorted_names]


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

    # Sort classes based on inheritance hierarchy
    sorted_classes = sort_classes_by_inheritance(dsl_classes)

    # Generate semantic classes in sorted order
    generated = [
        generate_semantic_class(class_name, cls)
        for class_name, cls in sorted_classes
    ]

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
        f.write("\n\n".join(generated))
        f.write("\n\n")

    # Format the file with Ruff
    format_with_ruff(str(output_path))


def format_with_ruff(file_path: str) -> None:
    """Format the given file using Ruff."""
    try:
        subprocess.run(["ruff", "check", "--fix", file_path], check=True)
        subprocess.run(["ruff", "format", file_path], check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error while formatting with Ruff: {e}")


def generate_semantic_class(class_name: str, cls: type) -> str:
    """Generate a semantic class from a DSL class."""
    semantic_name = f"{class_name}"

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
            semantic_base = f"{base.__name__}"
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
                semantic_type = dsl_to_semantic_type_name(field_type)

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
    from enum import Enum

    if field_default is PydanticUndefined or field_default is ...:
        default_part = "..."
    elif field_default is None:
        default_part = "None"
    elif isinstance(field_default, Enum):
        # Handle enum values (like DecoderFormat.json) - check this before str since some enums inherit from str
        enum_class_name = field_default.__class__.__name__
        enum_value_name = field_default.name
        default_part = f"{enum_class_name}.{enum_value_name}"
    elif isinstance(field_default, str):
        default_part = f'"{field_default}"'
    elif hasattr(
        field_default, "__name__"
    ):  # Callable or other objects with names
        # Handle other defaults with names
        if hasattr(field_default, "__module__") and hasattr(
            field_default, "__qualname__"
        ):
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
