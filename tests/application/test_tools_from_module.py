"""Tests for tools_from_module converter."""

from __future__ import annotations

import inspect
import sys
import textwrap
from pathlib import Path
from typing import Union
from unittest.mock import MagicMock, Mock

import pytest
from pydantic import BaseModel

from qtype.application.converters.tools_from_module import (
    _create_tool_from_function,
    _get_module_functions,
    _map_python_type_to_type_str,
    _map_python_type_to_variable_type,
    _pydantic_to_custom_types,
    tools_from_module,
)
from qtype.base.types import PrimitiveTypeEnum
from qtype.dsl.model import PythonFunctionTool


class SampleModel(BaseModel):
    """Sample model for testing."""

    name: str
    age: int


class OptionalModel(BaseModel):
    """Model with optional field."""

    name: str
    age: Union[int, None]


class ListModel(BaseModel):
    """Model with list field."""

    items: list[str]


@pytest.fixture
def temp_module(tmp_path: Path):
    """Create temporary module for testing."""
    created_modules = []

    def _create(code: str, name: str = "test_module"):
        module_file = tmp_path / f"{name}.py"
        module_file.write_text(textwrap.dedent(code))
        sys.path.insert(0, str(tmp_path))
        created_modules.append(name)

        # Clear any existing module cache
        if name in sys.modules:
            del sys.modules[name]

        return name

    yield _create

    # Cleanup
    for name in created_modules:
        if name in sys.modules:
            del sys.modules[name]
    if str(tmp_path) in sys.path:
        sys.path.remove(str(tmp_path))


@pytest.fixture
def mock_func_info():
    """Sample function metadata."""
    return {
        "callable": lambda x: x,
        "signature": inspect.signature(lambda x: x),
        "docstring": "Test function",
        "parameters": [
            {
                "name": "x",
                "type": str,
                "default": inspect.Parameter.empty,
                "kind": inspect.Parameter.POSITIONAL_OR_KEYWORD,
            }
        ],
        "return_type": str,
        "module": "test_module",
    }


def test_tools_from_module_success(temp_module):
    """Test successful tool extraction."""
    module_name = temp_module(
        """
        def add(a: int, b: int) -> int:
            '''Add two numbers.'''
            return a + b

        def greet(name: str, greeting: str = "Hello") -> str:
            return f"Hello, {name}!"
    """,
        "success_module",
    )

    tools, custom_types = tools_from_module(module_name)

    assert len(tools) == 2
    assert len(custom_types) == 0
    assert {t.name for t in tools} == {"add", "greet"}

    add_tool = next(t for t in tools if t.name == "add")
    assert add_tool.description == "Add two numbers."
    assert add_tool.inputs is not None
    assert len(add_tool.inputs) == 2
    assert "a" in add_tool.inputs
    assert "b" in add_tool.inputs
    assert add_tool.inputs["a"].type == PrimitiveTypeEnum.int
    assert add_tool.inputs["b"].type == PrimitiveTypeEnum.int
    assert not add_tool.inputs["a"].optional
    assert not add_tool.inputs["b"].optional

    greet_tool = next(t for t in tools if t.name == "greet")
    assert greet_tool.inputs is not None
    assert len(greet_tool.inputs) == 2
    assert "name" in greet_tool.inputs
    assert "greeting" in greet_tool.inputs
    assert greet_tool.inputs["name"].type == PrimitiveTypeEnum.text
    assert greet_tool.inputs["greeting"].type == PrimitiveTypeEnum.text
    assert not greet_tool.inputs["name"].optional
    assert greet_tool.inputs["greeting"].optional


def test_tools_from_module_errors():
    """Test error cases for tools_from_module."""
    # Import error
    with pytest.raises(
        ImportError, match="Cannot import module 'nonexistent'"
    ):
        tools_from_module("nonexistent")


def test_tools_from_module_no_functions(temp_module):
    """Test no functions found."""
    module_name = temp_module("# Empty module", "empty_module")
    with pytest.raises(
        ValueError, match="No public functions found in module 'empty_module'"
    ):
        tools_from_module(module_name)


def test_get_module_functions_success():
    """Test function extraction from module."""

    def sample_func(x: int, y: str) -> str:
        return f"{x}: {y}"

    sample_func.__module__ = "test_module"

    module = MagicMock()
    module.sample_func = sample_func
    module._private = lambda: None  # Should be ignored

    functions = _get_module_functions("test_module", module)

    assert "sample_func" in functions
    assert "_private" not in functions
    assert functions["sample_func"]["return_type"] == "str"


def test_get_module_functions_no_return_annotation():
    """Test error when function lacks return annotation."""

    def bad_func(x: int):
        return x

    bad_func.__module__ = "test_module"
    module = MagicMock()
    module.bad_func = bad_func

    with pytest.raises(ValueError, match="must have a return type annotation"):
        _get_module_functions("test_module", module)


@pytest.mark.parametrize(
    "docstring,expected",
    [
        ("Test function\nWith details", "Test function"),
        ("", "Function test_func"),
        (None, "Function test_func"),
    ],
)
def test_create_tool_from_function(mock_func_info, docstring, expected):
    """Test tool creation from function metadata."""
    mock_func_info["docstring"] = docstring
    custom_types = {}

    tool = _create_tool_from_function(
        "test_func", mock_func_info, custom_types
    )

    assert isinstance(tool, PythonFunctionTool)
    assert tool.id == "test_module.test_func"
    assert tool.description == expected
    assert tool.inputs is not None
    assert len(tool.inputs) == 1
    assert "x" in tool.inputs
    assert tool.inputs["x"].type == PrimitiveTypeEnum.text
    assert not tool.inputs["x"].optional


def test_create_tool_no_parameters():
    """Test tool creation with no parameters."""
    func_info = {
        "callable": lambda: "result",
        "signature": inspect.signature(lambda: "result"),
        "docstring": "No params",
        "parameters": [],
        "return_type": str,
        "module": "test_module",
    }

    tool = _create_tool_from_function("no_params", func_info, {})
    assert tool.inputs == {}
    assert len(tool.outputs) > 0
    assert "result" in tool.outputs
    assert tool.outputs["result"].type == PrimitiveTypeEnum.text
    assert not tool.outputs["result"].optional


@pytest.mark.parametrize(
    "model_cls,expected_props",
    [
        (SampleModel, {"name": "text", "age": "int"}),
        (OptionalModel, {"name": "text", "age": "int?"}),
        (ListModel, {"items": "list[text]"}),
    ],
)
def test_pydantic_to_custom_types(model_cls, expected_props):
    """Test Pydantic model conversion to custom types."""
    custom_types = {}
    result = _pydantic_to_custom_types(model_cls, custom_types)

    assert result == model_cls.__name__
    assert model_cls.__name__ in custom_types

    custom_type = custom_types[model_cls.__name__]
    assert custom_type.properties == expected_props


def test_pydantic_already_processed():
    """Test already processed model returns existing name."""
    from typing import cast

    from qtype.dsl.model import CustomType

    mock_custom_type = cast(CustomType, Mock())
    custom_types = {"SampleModel": mock_custom_type}
    result = _pydantic_to_custom_types(SampleModel, custom_types)

    assert result == "SampleModel"
    assert len(custom_types) == 1


def test_pydantic_no_annotation():
    """Test error for field without annotation."""
    mock_model = Mock()
    mock_model.__name__ = "BadModel"
    mock_model.model_fields = {"bad_field": Mock(annotation=None)}

    with pytest.raises(TypeError, match="must have a type hint"):
        _pydantic_to_custom_types(mock_model, {})  # type: ignore


@pytest.mark.parametrize(
    "python_type,expected",
    [
        (str, PrimitiveTypeEnum.text),
        (int, PrimitiveTypeEnum.int),
        (bool, PrimitiveTypeEnum.boolean),
    ],
)
def test_map_python_type_to_variable_type_primitives(python_type, expected):
    """Test mapping primitive types."""
    result = _map_python_type_to_variable_type(python_type, {})
    assert result == expected


def test_map_python_type_pydantic_model():
    """Test mapping Pydantic model."""
    custom_types = {}
    result = _map_python_type_to_variable_type(SampleModel, custom_types)

    assert result == "SampleModel"
    assert "SampleModel" in custom_types


def test_map_python_type_unsupported():
    """Test error for unsupported type."""
    with pytest.raises(ValueError, match="Unsupported Python type"):
        _map_python_type_to_variable_type(dict, {})


@pytest.mark.parametrize(
    "python_type,expected",
    [
        (str, "text"),
        (int, "int"),
        (SampleModel, "SampleModel"),
    ],
)
def test_map_python_type_to_type_str(python_type, expected):
    """Test type to string mapping."""
    result = _map_python_type_to_type_str(python_type, {})
    assert result == expected
