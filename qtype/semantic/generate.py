import argparse
import inspect
import subprocess
from enum import Enum
from functools import partial
from pathlib import Path
from textwrap import dedent
from typing import Annotated, Any, Literal, Union, get_args, get_origin

import networkx as nx

import qtype.base.types as base_types
import qtype.dsl.model as dsl


def _is_dsl_type(type_obj: Any) -> bool:
    """Check if a type is a DSL type that should be converted to semantic."""
    if not hasattr(type_obj, "__name__"):
        return False

    # Check if it's defined in the DSL module
    return (
        hasattr(type_obj, "__module__")
        and (
            type_obj.__module__ == dsl.__name__
            or type_obj.__module__ == base_types.__name__
        )
        and not type_obj.__name__.startswith("_")
    )


FIELDS_TO_IGNORE = {"Application.references"}
TYPES_TO_IGNORE = {
    "CustomType",
    "DecoderFormat",
    "Document",
    "ListType",
    "PrimitiveTypeEnum",
    "StrictBaseModel",
    "TypeDefinition",
    "ToolParameter",
    "Variable",
}

FROZEN_TYPES = {
    "AuthorizationProvider",
    "DocumentIndex",
    "EmbeddingModel",
    "Index",
    "Memory",
    "Model",
    "Tool",
    "VectorIndex",
}


def sort_classes_by_inheritance(
    classes: list[tuple[str, type]],
) -> list[tuple[str, type]]:
    """Sort classes based on their inheritance hierarchy."""
    graph: nx.DiGraph = nx.DiGraph()
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
        f.write(
            dedent('''
            """
            Semantic Intermediate Representation models.

            This module contains the semantic models that represent a resolved QType
            specification where all ID references have been replaced with actual object
            references.

            Generated automatically with command:
            qtype generate semantic-model

            Types are ignored since they should reflect dsl directly, which is type checked.
            """

        ''').lstrip()
        )

        # Write imports
        f.write(
            dedent("""
            from __future__ import annotations

            from functools import partial
            from typing import Any, Literal, Union

            from pydantic import BaseModel, Field, RootModel

            # Import enums, mixins, and type aliases
            from qtype.base.types import BatchableStepMixin, BatchConfig, CachedStepMixin, ConcurrencyConfig, ConcurrentStepMixin  # noqa: F401
            from qtype.dsl.model import (  # noqa: F401
                CustomType,
                DecoderFormat,
                ListType,
                PrimitiveTypeEnum,
                StepCardinality,
                ToolParameter
            )
            from qtype.dsl.model import Variable as DSLVariable  # noqa: F401
            from qtype.dsl.model import VariableType  # noqa: F401
            from qtype.semantic.base_types import ImmutableModel

        """).lstrip()
        )

        # Write the new variable class
        f.write(
            dedent('''
            class Variable(DSLVariable, BaseModel):
                """Semantic version of DSL Variable with ID references resolved."""
                value: Any | None = Field(None, description="The value of the variable")
                def is_set(self) -> bool:
                    return self.value is not None

        ''').lstrip()
        )

        # Write classes
        f.write("\n\n".join(generated))

        # Write the DocumentType
        f.write(
            dedent("""\n\n
                DocumentType = Union[
                    Application,
                    AuthorizationProviderList,
                    ModelList,
                    ToolList,
                    TypeList,
                    VariableList,
                ]
                       """)
        )

    # Format the file with Ruff
    format_with_ruff(str(output_path))


def format_with_ruff(file_path: str) -> None:
    """Format the given file using Ruff and isort to match pre-commit configuration."""
    # Apply the same formatting as pre-commit but only to the specific file
    # Use --force-exclude to match pre-commit behavior exactly
    subprocess.run(["ruff", "check", "--fix", file_path], check=True)
    subprocess.run(
        ["ruff", "format", "--force-exclude", file_path], check=True
    )
    subprocess.run(["isort", file_path], check=True)


def _get_union_args(type_annotation):
    """Extract union args from a type, handling Annotated types."""
    if get_origin(type_annotation) is Annotated:
        # For Annotated[Union[...], ...], get the Union part
        union_type = get_args(type_annotation)[0]
        return get_args(union_type)
    else:
        return get_args(type_annotation)


DSL_ONLY_UNION_TYPES = {
    _get_union_args(dsl.ToolType): "Tool",
    _get_union_args(dsl.StepType): "Step",
    _get_union_args(dsl.AuthProviderType): "AuthorizationProvider",
    _get_union_args(dsl.SecretManagerType): "SecretManager",
    _get_union_args(dsl.SourceType): "Source",
    _get_union_args(dsl.IndexType): "Index",
    _get_union_args(dsl.ModelType): "Model",
}


def _is_dsl_only_union(args_without_str_none: tuple) -> tuple[bool, str]:
    """
    Check if union represents a DSL-only type pattern.

    Args:
        args_without_str_none: Union args with str and None filtered out

    Returns:
        Tuple of (is_dsl_only, semantic_type_name)
    """
    if args_without_str_none and args_without_str_none in DSL_ONLY_UNION_TYPES:
        return True, DSL_ONLY_UNION_TYPES[args_without_str_none]
    return False, ""


def _resolve_optional_collection(args: tuple, has_none: bool) -> str | None:
    """
    Handle list|None -> list pattern (empty collection = None).

    Args:
        args: Union type arguments
        has_none: Whether None is in the union

    Returns:
        Resolved type name if pattern matches, None otherwise
    """
    if len(args) == 2 and has_none:
        collection_types = [
            arg for arg in args if get_origin(arg) in {list, dict}
        ]
        if collection_types:
            return dsl_to_semantic_type_name(collection_types[0])
    return None


def _is_id_reference_pattern(
    args: tuple, has_str: bool, has_secret_ref: bool
) -> bool:
    """
    Check if union represents an ID reference pattern (str | Type).

    ID references allow DSL to use string IDs that get resolved to objects
    in the semantic model. Exception: str | SecretReference stays as-is.

    Args:
        args: Union type arguments
        has_str: Whether str is in the union
        has_secret_ref: Whether SecretReference is in the union

    Returns:
        True if this is an ID reference pattern
    """
    return (
        any(_is_dsl_type(arg) for arg in args)
        and has_str
        and not has_secret_ref
    )


def _strip_str_from_union(args: tuple) -> tuple:
    """
    Remove str component from union for ID reference pattern.

    Args:
        args: Union type arguments

    Returns:
        Args with str filtered out
    """
    return tuple(arg for arg in args if arg is not str)


def _transform_union_type(args: tuple) -> str:
    """
    Transform Union types, handling string ID references and special cases.

    This function handles the semantic type generation for union types,
    with special handling for:
    - DSL-only types (e.g., ToolType -> Tool)
    - ID references (str | SomeType -> SomeType)
    - SecretReference (str | SecretReference stays as-is)
    - Optional types (Type | None)

    Args:
        args: Tuple of types in the union

    Returns:
        String representation of the semantic type
    """
    # Import SecretReference for direct type comparison
    from qtype.dsl.model import SecretReference

    # Pre-compute type characteristics
    args_without_str_none = tuple(
        arg for arg in args if arg is not str and arg is not type(None)
    )
    has_none = any(arg is type(None) for arg in args)
    has_str = any(arg is str for arg in args)
    has_secret_ref = any(arg is SecretReference for arg in args)

    # Handle DSL-only union types (e.g., ToolType -> Tool)
    is_dsl_only, dsl_semantic_name = _is_dsl_only_union(args_without_str_none)
    if is_dsl_only:
        return dsl_semantic_name + " | None" if has_none else dsl_semantic_name

    # Handle list | None -> list (empty list is equivalent to None)
    if resolved_collection := _resolve_optional_collection(args, has_none):
        return resolved_collection

    # Handle ID references: str | SomeType -> SomeType
    # Exception: str | SecretReference should remain as-is
    if _is_id_reference_pattern(args, has_str, has_secret_ref):
        args = _strip_str_from_union(args)

    # Convert remaining types to semantic type names
    return " | ".join(dsl_to_semantic_type_name(a) for a in args)


def dsl_to_semantic_type_name(field_type: Any) -> str:
    """Transform a DSL field type to a semantic field type."""

    # Handle ForwardRef objects
    if hasattr(field_type, "__forward_arg__"):
        # Extract the string from ForwardRef and process it
        forward_ref_str = field_type.__forward_arg__
        actual_type = eval(forward_ref_str, dict(vars(dsl)))
        return dsl_to_semantic_type_name(actual_type)

    # Handle Union types (including | syntax)
    origin = get_origin(field_type)
    args = get_args(field_type)

    # Handle Reference types - unwrap to get the actual type
    # Reference[T] is a Pydantic generic model, so get_origin returns None
    # Instead, check if Reference is in the MRO
    if (
        hasattr(field_type, "__mro__")
        and base_types.Reference in field_type.__mro__
    ):
        # Reference[T] becomes just T in semantic model
        # The actual type parameter is in __pydantic_generic_metadata__ for Pydantic generic models
        if hasattr(field_type, "__pydantic_generic_metadata__"):
            metadata = field_type.__pydantic_generic_metadata__
            if "args" in metadata and metadata["args"]:
                return dsl_to_semantic_type_name(metadata["args"][0])
        return "Any"  # Fallback for untyped Reference

    # Handle Annotated types - extract the underlying type
    if origin is Annotated:
        # For Annotated[SomeType, ...], we want to process SomeType
        if args:
            return dsl_to_semantic_type_name(args[0])

    if origin is Union or (
        hasattr(field_type, "__class__")
        and field_type.__class__.__name__ == "UnionType"
    ):
        return _transform_union_type(args)

    # Handle Literal types
    if origin is Literal:
        # Format literal values
        literal_values = []
        for arg in args:
            if isinstance(arg, Enum):
                # Keep the enum reference for semantic models (e.g., StepCardinality.one)
                # not the string value
                enum_class_name = arg.__class__.__name__
                enum_value_name = arg.name
                literal_values.append(f"{enum_class_name}.{enum_value_name}")
            elif isinstance(arg, str):
                literal_values.append(f'"{arg}"')
            else:
                literal_values.append(str(arg))
        return f"Literal[{', '.join(literal_values)}]"

    # Handle list types
    if origin is list:
        if args:
            inner_type = dsl_to_semantic_type_name(args[0])
            return f"list[{inner_type}]"
        return "list"

    # Handle dict types
    if origin is dict:
        if len(args) == 2:
            key_type = dsl_to_semantic_type_name(args[0])
            value_type = dsl_to_semantic_type_name(args[1])
            return f"dict[{key_type}, {value_type}]"
        return "dict"

    # Handle basic types
    if hasattr(field_type, "__name__"):
        type_name = field_type.__name__
        if _is_dsl_type(field_type) and type_name not in TYPES_TO_IGNORE:
            return str(type_name)
        if type_name == "NoneType":
            return "None"
        return str(type_name)

    return str(field_type)


def generate_semantic_class(class_name: str, cls: type) -> str:
    """Generate a semantic class from a DSL class."""
    semantic_name = f"{class_name}"

    # Get class docstring
    docstring = cls.__doc__ or f"Semantic version of {class_name}."

    # Determine inheritance
    if class_name in FROZEN_TYPES:
        # If this is a frozen type, we use ImmutableModel instead of BaseModel
        inheritance = "ImmutableModel"
    else:
        inheritance = "BaseModel"
    if inspect.isabstract(cls):
        inheritance += ", ABC"

    # Collect all base classes from DSL and base_types modules
    base_classes = []
    for base in cls.__bases__:
        if (
            hasattr(base, "__module__")
            and (
                base.__module__ == dsl.__name__
                or base.__module__ == base_types.__name__
            )
            and base.__name__ not in TYPES_TO_IGNORE
            and not base.__name__.startswith("_")
        ):
            base_classes.append(base)

    # Build inheritance string
    if base_classes:
        # Process DSL classes first, then mixins
        dsl_bases = [
            b.__name__ for b in base_classes if b.__module__ == dsl.__name__
        ]
        mixin_bases = [
            b.__name__
            for b in base_classes
            if b.__module__ == base_types.__name__
        ]

        if dsl_bases:
            # Inherit from the DSL class
            semantic_base = dsl_bases[0]
            if inspect.isabstract(cls):
                inheritance = f"ABC, {semantic_base}"
            else:
                inheritance = semantic_base
            if semantic_name == "Tool":
                # Tools should inherit from Step and be immutable
                inheritance = f"{semantic_base}, ImmutableModel"

        # Add mixins to the inheritance - must come BEFORE BaseModel for correct MRO
        if mixin_bases:
            if inheritance == "BaseModel":
                # Mixins must come before BaseModel
                inheritance = f"{', '.join(mixin_bases)}, BaseModel"
            else:
                # If we have other bases, append mixins
                inheritance = f"{inheritance}, {', '.join(mixin_bases)}"

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
                field_default_factory = field_info.default_factory
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
                    field_name,
                    semantic_type,
                    field_default,
                    field_default_factory,
                    field_description,
                )
                fields.append(field_def)

    # Build class definition
    lines = [f"class {semantic_name}({inheritance}):"]
    lines.append(f'    """{docstring}"""')
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
    field_default_factory: Any,
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

    # Check if there's a default_factory
    if field_default_factory is not None:
        # Handle default_factory - check if it's a partial
        if isinstance(field_default_factory, partial):
            # For partial, we need to serialize it properly
            func_name = field_default_factory.func.__name__
            # Get the keyword arguments from the partial
            kwargs_str = ", ".join(
                f"{k}={v}" if not isinstance(v, str) else f'{k}="{v}"'
                for k, v in field_default_factory.keywords.items()
            )
            default_part = (
                f"default_factory=partial({func_name}, {kwargs_str})"
            )
        else:
            # Regular factory function
            factory_name = getattr(
                field_default_factory, "__name__", str(field_default_factory)
            )
            default_part = f"default_factory={factory_name}"
    elif field_default is PydanticUndefined or field_default is ...:
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
    # If using default_factory, don't include it in field_parts list initially
    if field_default_factory is not None:
        field_parts = []
    else:
        field_parts = [default_part]

    if field_description:
        # Escape quotes and handle multiline descriptions
        escaped_desc = field_description.replace('"', '\\"').replace(
            "\n", "\\n"
        )
        field_parts.append(f'description="{escaped_desc}"')
    if alias_part:
        field_parts.append(alias_part.lstrip(", "))

    # Handle default_factory in the Field() call
    if field_default_factory is not None:
        if field_parts:
            field_def = f"Field({default_part}, {', '.join(field_parts)})"
        else:
            field_def = f"Field({default_part})"
    else:
        field_def = f"Field({', '.join(field_parts)})"

    return f"    {field_name}: {field_type} = {field_def}"
