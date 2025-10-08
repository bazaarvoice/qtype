"""Documentation generation utilities for DSL classes."""

import inspect
from pathlib import Path
from typing import Any, Type, Union, get_args, get_origin

import qtype.dsl.model as dsl
from qtype.base.types import PrimitiveTypeEnum


def _format_type_name(field_type: Any) -> str:
    """Format a type annotation for display in documentation."""
    # Handle ForwardRef objects
    if hasattr(field_type, "__forward_arg__"):
        return str(field_type.__forward_arg__)

    # Handle Union types (including | syntax)
    origin = get_origin(field_type)
    args = get_args(field_type)

    if origin is Union or (
        hasattr(field_type, "__class__")
        and field_type.__class__.__name__ == "UnionType"
    ):
        return " | ".join(_format_type_name(arg) for arg in args)

    # Handle list types
    if origin is list:
        if args:
            inner_type = _format_type_name(args[0])
            return f"list[{inner_type}]"
        return "list"

    # Handle dict types
    if origin is dict:
        if len(args) == 2:
            key_type = _format_type_name(args[0])
            value_type = _format_type_name(args[1])
            return f"dict[{key_type}, {value_type}]"
        return "dict"

    # Handle basic types
    if hasattr(field_type, "__name__"):
        type_name = field_type.__name__
        if type_name == "NoneType":
            return "None"
        return str(type_name)

    return str(field_type)


def generate_class_docstring(output_file: Path, cls: Type[Any]) -> None:
    """Generates markdown documentation for a given DSL class.

    The generated markdown contains a table of the class members and their descriptions.
    The docstring of the class is used as the main description.
    The field descriptions from Pydantic model_fields are used to describe each member.
    """
    class_name = cls.__name__
    docstring = cls.__doc__ or "No documentation available."

    # new lines in the docstring often have indentation, which we want to remove
    docstring = "\n".join(
        line.strip() for line in docstring.splitlines() if line.strip()
    )

    with output_file.open("w", encoding="utf-8") as file:
        file.write(f"### {class_name}\n\n{docstring}\n\n")

        # Handle Pydantic models by checking for model_fields
        if hasattr(cls, "model_fields") and hasattr(cls, "__annotations__"):
            # Process Pydantic model fields
            for field_name in cls.__annotations__:
                if field_name in cls.model_fields:
                    field_info = cls.model_fields[field_name]
                    field_type = field_info.annotation
                    field_description = getattr(
                        field_info, "description", None
                    )

                    # Format the type name for display
                    type_name = _format_type_name(field_type)

                    # Use field description or fallback
                    description = (
                        field_description or "(No documentation available.)"
                    )

                    file.write(
                        f"- **{field_name}** (`{type_name}`): {description}\n"
                    )
        else:
            # Fallback to inspect.getmembers for non-Pydantic classes
            members = inspect.getmembers(
                cls, lambda a: not inspect.isroutine(a)
            )
            for name, value in members:
                if not name.startswith("_"):
                    member_doc = (
                        value.__doc__ or "(No documentation available.)"
                    )
                    file.write(f"- **{name}**: {member_doc}\n")


def generate_documentation(output_prefix: Path) -> None:
    """Generates markdown documentation for all DSL classes.
    The documentation is saved in the specified output prefix directory.
    Args:
        output_prefix (Path): The directory where the documentation files will be saved.
    """
    # erase everything in the output directory
    output_prefix.mkdir(parents=True, exist_ok=True)
    for item in output_prefix.iterdir():
        if item.is_dir():
            for subitem in item.iterdir():
                if subitem.is_file():
                    subitem.unlink()
            item.rmdir()
        elif item.is_file():
            item.unlink()

    # Get all classes from the DSL model module
    for name, cls in inspect.getmembers(dsl, inspect.isclass):  # noqa: F821
        if cls.__module__ == dsl.__name__ and not name.startswith("_"):
            generate_class_docstring(output_prefix / f"{name}.md", cls)
    generate_class_docstring(
        output_prefix / "PrimitiveTypeEnum.md", PrimitiveTypeEnum
    )

    for name, cls in inspect.getmembers(dsl.domain_types, inspect.isclass):  # noqa: F821
        if cls.__module__ == dsl.domain_types.__name__ and not name.startswith(
            "_"
        ):
            generate_class_docstring(output_prefix / f"{name}.md", cls)
