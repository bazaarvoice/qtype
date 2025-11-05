"""Helper mixin for creating LlamaIndex FunctionTools from QType definitions."""

from __future__ import annotations

import importlib
import logging
from typing import Any

from llama_index.core.bridge.pydantic import BaseModel
from llama_index.core.bridge.pydantic import Field as PydanticField
from llama_index.core.tools import FunctionTool, ToolMetadata
from pydantic import create_model

from qtype.base.types import PrimitiveTypeEnum
from qtype.dsl.model import ListType
from qtype.dsl.types import PRIMITIVE_TO_PYTHON_TYPE
from qtype.semantic.model import APITool, PythonFunctionTool, ToolParameter

logger = logging.getLogger(__name__)


class FunctionToolHelper:
    """Mixin providing utilities for creating LlamaIndex FunctionTools.

    This mixin provides methods to convert QType tool definitions
    (APITool, PythonFunctionTool) into LlamaIndex FunctionTool instances
    with proper metadata and Pydantic schemas.
    """

    @staticmethod
    def _qtype_type_to_python_type(
        param: ToolParameter,
    ) -> type:
        """Convert QType ToolParameter type to Python type for Pydantic.

        The param.type has already been resolved during semantic model
        creation, so we just need to convert it to the appropriate Python
        type:
        - Primitive types → Python type via PRIMITIVE_TO_PYTHON_TYPE
        - BaseModel subclasses (domain/custom types) → pass through
        - List types → list[element_type] (recursively resolved)
        - Unknown → str

        Args:
            param: The QType ToolParameter to convert.

        Returns:
            Python type suitable for Pydantic field annotation.
        """
        # Handle primitive types
        if isinstance(param.type, PrimitiveTypeEnum):
            return PRIMITIVE_TO_PYTHON_TYPE[param.type]

        # Handle list types - recursively resolve element type
        if isinstance(param.type, ListType):
            # Create a mock parameter with the element type to recursively
            # resolve it
            element_param = ToolParameter(
                type=param.type.element_type,
                optional=False,
            )
            element_python_type = (
                FunctionToolHelper._qtype_type_to_python_type(element_param)
            )
            return list[element_python_type]  # type: ignore[valid-type]

        # Handle domain/custom types (BaseModel subclasses)
        if isinstance(param.type, type) and issubclass(param.type, BaseModel):
            return param.type

        # For unresolved string references or unknown types, default to str
        return str

    @staticmethod
    def _create_fn_schema(
        tool_name: str,
        inputs: dict[str, ToolParameter],
    ) -> type[BaseModel] | None:
        """Create a Pydantic model from QType tool input parameters.

        Args:
            tool_name: Name of the tool (used for model name).
            inputs: Dictionary of input parameter names to ToolParameter.

        Returns:
            Pydantic BaseModel class representing the tool's input schema.
            Returns an empty BaseModel if there are no inputs (required by
            LlamaIndex ReActAgent).
        """
        # Build field definitions for Pydantic model
        # Each field is a tuple of (type_annotation, field_info)
        field_definitions: dict[str, Any] = {}

        for param_name, param in inputs.items():
            python_type = FunctionToolHelper._qtype_type_to_python_type(param)

            # Create field with optional annotation
            if param.optional:
                field_definitions[param_name] = (
                    python_type | None,  # type: ignore[valid-type]
                    PydanticField(default=None),
                )
            else:
                field_definitions[param_name] = (
                    python_type,
                    PydanticField(...),
                )

        # Create dynamic Pydantic model
        model_name = f"{tool_name.replace('-', '_').replace('.', '_')}_Input"
        return create_model(model_name, **field_definitions)  # type: ignore[call-overload]

    @staticmethod
    def _create_tool_metadata(
        tool: APITool | PythonFunctionTool,
    ) -> ToolMetadata:
        """Create ToolMetadata from a QType tool definition.

        Args:
            tool: The QType tool (API or Python function).

        Returns:
            ToolMetadata for use with FunctionTool.
        """
        # Create Pydantic schema from tool inputs
        fn_schema = FunctionToolHelper._create_fn_schema(
            tool.name, tool.inputs
        )

        return ToolMetadata(
            name=tool.name,
            description=tool.description,
            fn_schema=fn_schema,
            return_direct=False,
        )

    def _create_python_function_tool(
        self, tool: PythonFunctionTool
    ) -> FunctionTool:
        """Create a FunctionTool for a Python function.

        For Python functions, we import and wrap the actual function,
        allowing LlamaIndex to access its signature while routing
        execution through our wrapper for consistent error handling,
        logging, and telemetry across all tool invocations.

        Args:
            tool: The Python function tool definition.

        Returns:
            LlamaIndex FunctionTool wrapping the Python function.

        Raises:
            ValueError: If the function cannot be imported.
        """
        try:
            # Import the actual Python function
            module = importlib.import_module(tool.module_path)
            function = getattr(module, tool.function_name, None)
            if function is None:
                raise ValueError(
                    (
                        f"Function '{tool.function_name}' not found in "
                        f"module '{tool.module_path}'"
                    )
                )

            # Create metadata from QType tool definition
            metadata = FunctionToolHelper._create_tool_metadata(tool)

            # Create wrapper that validates inputs using Pydantic schema
            # before calling the function through execution
            # This maintains consistent error handling and hooks
            async def wrapped_fn(**kwargs: Any) -> Any:
                # Keep original kwargs for streaming events (JSON-compatible)
                original_kwargs = kwargs.copy()

                # Validate and parse inputs using the Pydantic schema
                if metadata.fn_schema is not None:
                    validated_inputs = metadata.fn_schema(**kwargs)
                    # Convert Pydantic model to dict with Python native types
                    # (datetime objects, etc.)
                    kwargs = validated_inputs.model_dump(mode="python")

                # Pass both the validated kwargs and original for streaming
                return await self.execute_python_tool(  # type: ignore[attr-defined]
                    tool, kwargs, original_inputs=original_kwargs
                )

            return FunctionTool(
                fn=None,
                async_fn=wrapped_fn,
                metadata=metadata,
            )

        except (ImportError, AttributeError) as e:
            raise ValueError(
                (
                    f"Failed to import Python function "
                    f"'{tool.function_name}' "
                    f"from '{tool.module_path}': {e}"
                )
            ) from e

    def _create_api_tool(self, tool: APITool) -> FunctionTool:
        """Create a FunctionTool for an API endpoint.

        Wraps the API tool execution in a function that can be called
        by LlamaIndex agents, handling authentication, request formatting,
        and error handling consistently.

        Args:
            tool: The API tool definition.

        Returns:
            LlamaIndex FunctionTool wrapping the API tool execution.
        """
        # Create metadata from QType tool definition
        metadata = FunctionToolHelper._create_tool_metadata(tool)

        async def api_wrapper(**kwargs: Any) -> Any:
            """Wrapper function that executes the API tool."""
            # Keep original kwargs for streaming events (JSON-compatible)
            original_kwargs = kwargs.copy()

            # Validate and parse inputs using the Pydantic schema
            if metadata.fn_schema is not None:
                validated_inputs = metadata.fn_schema(**kwargs)
                # Convert Pydantic model to dict for execution
                kwargs = validated_inputs.model_dump(mode="python")

            # Pass both the validated kwargs and original for streaming
            return await self.execute_api_tool(  # type: ignore[attr-defined]
                tool, kwargs, original_inputs=original_kwargs
            )

        return FunctionTool(
            fn=None,
            async_fn=api_wrapper,
            metadata=metadata,
        )

    def _create_function_tool(
        self, tool: APITool | PythonFunctionTool
    ) -> FunctionTool:
        """Create a LlamaIndex FunctionTool from a QType tool definition.

        Dispatches to specialized methods based on tool type for optimal
        handling while maintaining consistent metadata generation.

        Args:
            tool: The QType tool (API or Python function).

        Returns:
            LlamaIndex FunctionTool wrapping the tool execution.

        Raises:
            ValueError: If the tool type is unsupported.
        """
        if isinstance(tool, PythonFunctionTool):
            return self._create_python_function_tool(tool)
        elif isinstance(tool, APITool):
            return self._create_api_tool(tool)
        else:
            raise ValueError(f"Unsupported tool type: {type(tool)}")
