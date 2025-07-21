"""
Tests for tool provider Python module functionality.
"""

import inspect
from datetime import date, datetime, time
from typing import Any, Type, Union, get_args, get_origin
from unittest.mock import Mock, patch

import pytest
from pydantic import BaseModel

from qtype.converters.tools_from_module import (
    TYPE_TO_VARIABLE,
    _create_tool_from_function,
    _get_module_functions,
    _map_python_type_to_variable_type,
    pydantic_to_object_definition,
    tools_from_module,
)
from qtype.dsl.model import (
    ArrayTypeDefinition,
    ObjectTypeDefinition,
    PrimitiveTypeEnum,
    PythonFunctionTool,
    Variable,
    VariableType,
)


class SamplePydanticModel(BaseModel):
    """Sample Pydantic model for testing type mapping."""

    name: str
    age: int
    active: bool


class TestLoadPythonModuleTools:
    """Test suite for tools_from_module function."""

    def test_successful_load_with_valid_module(self) -> None:
        """Test successful loading of tools from a valid module."""
        module_path = "tests.test_module_fixtures"

        with patch(
            "qtype.converters.tools_from_module.importlib.import_module"
        ) as mock_import:
            mock_module = Mock()
            mock_import.return_value = mock_module

            with patch(
                "qtype.converters.tools_from_module._get_module_functions"
            ) as mock_get_functions:
                mock_functions = {
                    "test_func": {
                        "callable": Mock(),
                        "signature": Mock(),
                        "docstring": "Test function",
                        "parameters": [],
                        "return_type": str,
                        "module": "tests.test_module_fixtures",
                    }
                }
                mock_get_functions.return_value = mock_functions

                with patch(
                    "qtype.converters.tools_from_module._create_tool_from_function"
                ) as mock_create_tool:
                    mock_tool = Mock(spec=PythonFunctionTool)
                    mock_create_tool.return_value = mock_tool

                    result = tools_from_module(module_path)

                    assert len(result) == 1
                    assert result[0] == mock_tool
                    mock_import.assert_called_once_with(
                        "tests.test_module_fixtures"
                    )
                    mock_get_functions.assert_called_once_with(
                        "tests.test_module_fixtures", mock_module
                    )
                    mock_create_tool.assert_called_once_with(
                        "test_func", mock_functions["test_func"]
                    )

    def test_import_error_handling(self) -> None:
        """Test handling of ImportError when module cannot be imported."""
        module_path = "nonexistent.module"

        with patch(
            "qtype.converters.tools_from_module.importlib.import_module"
        ) as mock_import:
            mock_import.side_effect = ImportError(
                "No module named 'nonexistent.module'"
            )

            with pytest.raises(
                ImportError, match="Cannot import module 'nonexistent.module'"
            ):
                tools_from_module(module_path)

    def test_no_functions_found_error(self) -> None:
        """Test handling when no public functions are found in module."""
        module_path = "tests.empty_module"

        with patch(
            "qtype.converters.tools_from_module.importlib.import_module"
        ) as mock_import:
            mock_module = Mock()
            mock_import.return_value = mock_module

            with patch(
                "qtype.converters.tools_from_module._get_module_functions"
            ) as mock_get_functions:
                mock_get_functions.return_value = {}

                with pytest.raises(
                    ValueError,
                    match="No public functions found in module 'tests.empty_module'",
                ):
                    tools_from_module(module_path)

    def test_multiple_functions_loaded(self) -> None:
        """Test loading multiple functions from a module."""
        module_path = "tests.multi_function_module"

        with patch(
            "qtype.converters.tools_from_module.importlib.import_module"
        ) as mock_import:
            mock_module = Mock()
            mock_import.return_value = mock_module

            with patch(
                "qtype.converters.tools_from_module._get_module_functions"
            ) as mock_get_functions:
                mock_functions = {
                    "func1": {
                        "callable": Mock(),
                        "signature": Mock(),
                        "docstring": "Function 1",
                        "parameters": [],
                        "return_type": str,
                        "module": "tests.multi_function_module",
                    },
                    "func2": {
                        "callable": Mock(),
                        "signature": Mock(),
                        "docstring": "Function 2",
                        "parameters": [],
                        "return_type": int,
                        "module": "tests.multi_function_module",
                    },
                }
                mock_get_functions.return_value = mock_functions

                with patch(
                    "qtype.converters.tools_from_module._create_tool_from_function"
                ) as mock_create_tool:
                    mock_tools = [
                        Mock(spec=PythonFunctionTool),
                        Mock(spec=PythonFunctionTool),
                    ]
                    mock_create_tool.side_effect = mock_tools

                    result = tools_from_module(module_path)

                    assert len(result) == 2
                    assert result == mock_tools
                    assert mock_create_tool.call_count == 2


class TestGetModuleFunctions:
    """Test suite for _get_module_functions function."""

    def test_extract_public_functions_only(self) -> None:
        """Test that only public functions are extracted."""
        mock_module = Mock()

        def public_func(x: int) -> str:
            """Public function."""
            return str(x)

        def _private_func(x: int) -> str:
            """Private function."""
            return str(x)

        public_func.__module__ = "test.module"
        _private_func.__module__ = "test.module"

        with patch(
            "qtype.converters.tools_from_module.inspect.getmembers"
        ) as mock_getmembers:
            # Mock getmembers to return only the functions (not the string)
            mock_getmembers.return_value = [
                ("public_func", public_func),
                ("_private_func", _private_func),
            ]

            result = _get_module_functions("test.module", mock_module)

            assert len(result) == 1
            assert "public_func" in result
            assert "_private_func" not in result

    def test_function_module_filtering(self) -> None:
        """Test that only functions from the target module are included."""
        mock_module = Mock()

        def local_func(x: int) -> str:
            """Local function."""
            return str(x)

        def external_func(x: int) -> str:
            """External function."""
            return str(x)

        local_func.__module__ = "target.module"
        external_func.__module__ = "other.module"

        mock_members = [
            ("local_func", local_func),
            ("external_func", external_func),
        ]

        with patch(
            "qtype.converters.tools_from_module.inspect.getmembers"
        ) as mock_getmembers:
            mock_getmembers.return_value = mock_members

            result = _get_module_functions("target.module", mock_module)

            assert len(result) == 1
            assert "local_func" in result
            assert "external_func" not in result

    def test_function_metadata_extraction(self) -> None:
        """Test that function metadata is correctly extracted."""
        mock_module = Mock()

        def test_func(x: int, y: str = "default") -> bool:
            """Test function with parameters."""
            return True

        test_func.__module__ = "test.module"

        mock_members = [("test_func", test_func)]

        with patch(
            "qtype.converters.tools_from_module.inspect.getmembers"
        ) as mock_getmembers:
            mock_getmembers.return_value = mock_members

            result = _get_module_functions("test.module", mock_module)

            assert len(result) == 1
            func_info = result["test_func"]

            assert func_info["callable"] == test_func
            assert func_info["docstring"] == "Test function with parameters."
            assert func_info["return_type"] is bool
            assert func_info["module"] == "test.module"
            assert len(func_info["parameters"]) == 2

            # Check first parameter
            param1 = func_info["parameters"][0]
            assert param1["name"] == "x"
            assert param1["type"] is int
            assert param1["default"] == inspect.Parameter.empty

            # Check second parameter
            param2 = func_info["parameters"][1]
            assert param2["name"] == "y"
            assert param2["type"] is str
            assert param2["default"] == "default"

    def test_missing_return_type_annotation(self) -> None:
        """Test that functions without return type annotations raise an error."""
        mock_module = Mock()

        def func_without_return_type(x: int):  # No return type annotation
            return x

        func_without_return_type.__module__ = "test.module"

        mock_members = [("func_without_return_type", func_without_return_type)]

        with patch(
            "qtype.converters.tools_from_module.inspect.getmembers"
        ) as mock_getmembers:
            mock_getmembers.return_value = mock_members

            with pytest.raises(
                ValueError,
                match="Function 'func_without_return_type' in module 'test.module' must have a return type annotation",
            ):
                _get_module_functions("test.module", mock_module)

    def test_empty_docstring_handling(self) -> None:
        """Test handling of functions with empty or missing docstrings."""
        mock_module = Mock()

        def func_no_docstring(x: int) -> str:
            return str(x)

        func_no_docstring.__module__ = "test.module"

        mock_members = [("func_no_docstring", func_no_docstring)]

        with patch(
            "qtype.converters.tools_from_module.inspect.getmembers"
        ) as mock_getmembers:
            mock_getmembers.return_value = mock_members

            result = _get_module_functions("test.module", mock_module)

            assert result["func_no_docstring"]["docstring"] == ""


class TestCreateToolFromFunction:
    """Test suite for _create_tool_from_function function."""

    def test_basic_tool_creation(self) -> None:
        """Test basic tool creation from function metadata."""
        func_info = {
            "callable": Mock(),
            "signature": Mock(),
            "docstring": "Test function for creating tools",
            "parameters": [
                {
                    "name": "x",
                    "type": int,
                    "default": inspect.Parameter.empty,
                    "kind": inspect.Parameter.POSITIONAL_OR_KEYWORD,
                },
                {
                    "name": "y",
                    "type": str,
                    "default": "default",
                    "kind": inspect.Parameter.POSITIONAL_OR_KEYWORD,
                },
            ],
            "return_type": bool,
            "module": "test.module",
        }

        with patch(
            "qtype.converters.tools_from_module._map_python_type_to_variable_type"
        ) as mock_map_type:
            mock_map_type.side_effect = [
                PrimitiveTypeEnum.int,
                PrimitiveTypeEnum.text,
                PrimitiveTypeEnum.boolean,
            ]

            tool = _create_tool_from_function("test_func", func_info)

            assert isinstance(tool, PythonFunctionTool)
            assert tool.id == "test.module.test_func"
            assert tool.name == "test_func"
            assert tool.module_path == "test.module"
            assert tool.function_name == "test_func"
            assert tool.description == "Test function for creating tools"

            # Check inputs
            assert tool.inputs is not None
            assert len(tool.inputs) == 2
            assert isinstance(tool.inputs[0], Variable)
            assert isinstance(tool.inputs[1], Variable)
            assert tool.inputs[0].id == "x"
            assert tool.inputs[0].type == PrimitiveTypeEnum.int
            assert tool.inputs[1].id == "y"
            assert tool.inputs[1].type == PrimitiveTypeEnum.text

            # Check outputs
            assert tool.outputs is not None
            assert len(tool.outputs) == 1
            assert isinstance(tool.outputs[0], Variable)
            assert tool.outputs[0].id == "test.module.test_func.result"
            assert tool.outputs[0].type == PrimitiveTypeEnum.boolean

    def test_no_parameters_function(self) -> None:
        """Test tool creation for function with no parameters."""
        func_info = {
            "callable": Mock(),
            "signature": Mock(),
            "docstring": "Function with no parameters",
            "parameters": [],
            "return_type": str,
            "module": "test.module",
        }

        with patch(
            "qtype.converters.tools_from_module._map_python_type_to_variable_type"
        ) as mock_map_type:
            mock_map_type.return_value = PrimitiveTypeEnum.text

            tool = _create_tool_from_function("no_params_func", func_info)

            assert tool.inputs is None
            assert tool.outputs is not None
            assert len(tool.outputs) == 1

    def test_multiline_docstring_description(self) -> None:
        """Test that only the first line of multiline docstring is used for description."""
        func_info = {
            "callable": Mock(),
            "signature": Mock(),
            "docstring": "First line description.\n\nSecond paragraph with more details.\nThird line.",
            "parameters": [],
            "return_type": str,
            "module": "test.module",
        }

        with patch(
            "qtype.converters.tools_from_module._map_python_type_to_variable_type"
        ) as mock_map_type:
            mock_map_type.return_value = PrimitiveTypeEnum.text

            tool = _create_tool_from_function("multiline_func", func_info)

            assert tool.description == "First line description."

    def test_empty_docstring_default_description(self) -> None:
        """Test default description when docstring is empty."""
        func_info = {
            "callable": Mock(),
            "signature": Mock(),
            "docstring": "",
            "parameters": [],
            "return_type": str,
            "module": "test.module",
        }

        with patch(
            "qtype.converters.tools_from_module._map_python_type_to_variable_type"
        ) as mock_map_type:
            mock_map_type.return_value = PrimitiveTypeEnum.text

            tool = _create_tool_from_function("empty_doc_func", func_info)

            assert tool.description == "Function empty_doc_func"


class TestMapPythonTypeToVariableType:
    """Test suite for _map_python_type_to_variable_type function."""

    def test_basic_type_mapping(self) -> None:
        """Test mapping of basic Python types to VariableType."""
        test_cases = [
            (str, PrimitiveTypeEnum.text),
            (int, PrimitiveTypeEnum.int),
            (float, PrimitiveTypeEnum.float),
            (bool, PrimitiveTypeEnum.boolean),
            (bytes, PrimitiveTypeEnum.bytes),
            (date, PrimitiveTypeEnum.date),
            (datetime, PrimitiveTypeEnum.datetime),
            (time, PrimitiveTypeEnum.time),
        ]

        for python_type, expected_variable_type in test_cases:
            result = _map_python_type_to_variable_type(python_type)
            assert result == expected_variable_type

    def test_none_type_handling(self) -> None:
        """Test handling of None type."""
        with pytest.raises(
            ValueError,
            match="Unsupported Python type 'None' for VariableType mapping",
        ):
            _map_python_type_to_variable_type(None)

    def test_unsupported_type_handling(self) -> None:
        """Test handling of unsupported types."""

        class CustomType:
            pass

        with pytest.raises(
            ValueError,
            match="Unsupported Python type .* for VariableType mapping",
        ):
            _map_python_type_to_variable_type(CustomType)

    def test_pydantic_model_mapping(self) -> None:
        """Test mapping of Pydantic model to dictionary structure."""
        result = _map_python_type_to_variable_type(SamplePydanticModel)

        assert isinstance(result, ObjectTypeDefinition)
        assert "name" in result.properties
        assert "age" in result.properties
        assert "active" in result.properties
        assert result.properties["name"] == PrimitiveTypeEnum.text
        assert result.properties["age"] == PrimitiveTypeEnum.int
        assert result.properties["active"] == PrimitiveTypeEnum.boolean

    def test_pydantic_model_without_schema_method(self) -> None:
        """Test handling of classes that don't have model_json_schema method."""

        class NonPydanticModel:
            pass

        with pytest.raises(
            ValueError,
            match="Unsupported Python type .* for VariableType mapping",
        ):
            _map_python_type_to_variable_type(NonPydanticModel)

    def test_list_type_mapping(self) -> None:
        """Test mapping of list type (bytes)."""
        result = _map_python_type_to_variable_type(bytes)
        assert result == PrimitiveTypeEnum.bytes


class TestIntegration:
    """Integration tests for the complete workflow."""

    def test_end_to_end_tool_loading(self) -> None:
        """Test complete workflow from provider to tools."""
        module_path = "test.integration.module"

        # Mock function info that would be returned by _get_module_functions
        mock_func_info = {
            "callable": Mock(),
            "signature": Mock(),
            "docstring": "Sample function that repeats text.",
            "parameters": [
                {
                    "name": "text",
                    "type": str,
                    "default": inspect.Parameter.empty,
                    "kind": inspect.Parameter.POSITIONAL_OR_KEYWORD,
                },
                {
                    "name": "count",
                    "type": int,
                    "default": 1,
                    "kind": inspect.Parameter.POSITIONAL_OR_KEYWORD,
                },
            ],
            "return_type": str,
            "module": "test.integration.module",
        }

        with patch(
            "qtype.converters.tools_from_module.importlib.import_module"
        ) as mock_import:
            mock_module = Mock()
            mock_import.return_value = mock_module

            with patch(
                "qtype.converters.tools_from_module._get_module_functions"
            ) as mock_get_functions:
                mock_get_functions.return_value = {
                    "sample_function": mock_func_info
                }

                tools = tools_from_module(module_path)

                assert len(tools) == 1
                tool = tools[0]

                assert isinstance(tool, PythonFunctionTool)
                assert tool.id == "test.integration.module.sample_function"
                assert tool.name == "sample_function"
                assert tool.module_path == "test.integration.module"
                assert tool.function_name == "sample_function"
                assert tool.description == "Sample function that repeats text."

                # Check inputs
                assert tool.inputs is not None
                assert len(tool.inputs) == 2
                assert isinstance(tool.inputs[0], Variable)
                assert isinstance(tool.inputs[1], Variable)
                assert tool.inputs[0].id == "text"
                assert tool.inputs[0].type == PrimitiveTypeEnum.text
                assert tool.inputs[1].id == "count"
                assert tool.inputs[1].type == PrimitiveTypeEnum.int

                # Check outputs
                assert tool.outputs is not None
                assert len(tool.outputs) == 1
                assert isinstance(tool.outputs[0], Variable)
                assert (
                    tool.outputs[0].id
                    == "test.integration.module.sample_function.result"
                )
                assert tool.outputs[0].type == PrimitiveTypeEnum.text

    def test_complex_pydantic_model_integration(self) -> None:
        """Test integration with complex Pydantic models."""

        class Metadata(BaseModel):
            created_at: datetime
            tags: list[str]

        class ComplexModel(BaseModel):
            name: str
            scores: list[float]
            metadata: Metadata

        module_path = "test.complex.module"

        # Mock function info with Pydantic model
        mock_func_info = {
            "callable": Mock(),
            "signature": Mock(),
            "docstring": "Function with complex Pydantic model input.",
            "parameters": [
                {
                    "name": "data",
                    "type": ComplexModel,
                    "default": inspect.Parameter.empty,
                    "kind": inspect.Parameter.POSITIONAL_OR_KEYWORD,
                },
            ],
            "return_type": bool,
            "module": "test.complex.module",
        }

        with patch(
            "qtype.converters.tools_from_module.importlib.import_module"
        ) as mock_import:
            mock_module = Mock()
            mock_import.return_value = mock_module

            with patch(
                "qtype.converters.tools_from_module._get_module_functions"
            ) as mock_get_functions:
                mock_get_functions.return_value = {
                    "complex_function": mock_func_info
                }

                tools = tools_from_module(module_path)

                assert len(tools) == 1
                tool = tools[0]

                # Check that the complex input type is handled
                assert tool.inputs is not None
                assert len(tool.inputs) == 1
                assert isinstance(tool.inputs[0], Variable)
                assert tool.inputs[0].id == "data"
                assert isinstance(tool.inputs[0].type, ObjectTypeDefinition)

                # Check that the boolean output type is handled
                assert tool.outputs is not None
                assert len(tool.outputs) == 1
                assert isinstance(tool.outputs[0], Variable)
                assert tool.outputs[0].type == PrimitiveTypeEnum.boolean


# Test fixtures for edge cases
class TestEdgeCases:
    """Test edge cases and error conditions."""

    def test_function_with_complex_annotations(self) -> None:
        """Test function with complex type annotations."""

        def complex_func(data: dict[str, list[int]]) -> tuple[str, int]:
            """Function with complex annotations."""
            return ("result", 42)

        complex_func.__module__ = "test.edge.module"

        mock_members = [("complex_func", complex_func)]

        with patch(
            "qtype.converters.tools_from_module.inspect.getmembers"
        ) as mock_getmembers:
            mock_getmembers.return_value = mock_members

            # The error should occur when trying to create tools from the function info
            with pytest.raises(
                ValueError,
                match="Unsupported Python type.*for VariableType mapping",
            ):
                func_info = _get_module_functions("test.edge.module", Mock())
                # This should raise an error when trying to create the tool
                _create_tool_from_function(
                    "complex_func", func_info["complex_func"]
                )

    def test_function_with_no_annotations(self) -> None:
        """Test function with no type annotations."""

        def no_annotations_func(x, y):  # No type annotations
            return x + y

        no_annotations_func.__module__ = "test.edge.module"

        mock_members = [("no_annotations_func", no_annotations_func)]

        with patch(
            "qtype.converters.tools_from_module.inspect.getmembers"
        ) as mock_getmembers:
            mock_getmembers.return_value = mock_members

            # This should raise an error for missing return type
            with pytest.raises(
                ValueError, match="must have a return type annotation"
            ):
                _get_module_functions("test.edge.module", Mock())


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
