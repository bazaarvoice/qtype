"""Test list type functionality."""

from qtype.base.types import PrimitiveTypeEnum
from qtype.dsl.model import ListType, Variable, _resolve_variable_type
from qtype.semantic.loader import load


def test_list_type_creation():
    """Test creating ListType instances."""
    list_type = ListType(element_type=PrimitiveTypeEnum.text)
    assert list_type.element_type == PrimitiveTypeEnum.text
    assert str(list_type) == "list[text]"


def test_list_type_variable():
    """Test creating variables with list types."""
    var = Variable(
        id="test_urls", type=ListType(element_type=PrimitiveTypeEnum.text)
    )
    assert var.id == "test_urls"
    assert isinstance(var.type, ListType)
    assert var.type.element_type == PrimitiveTypeEnum.text


def test_resolve_variable_type_list():
    """Test type resolution for list syntax."""
    # Test basic list type resolution
    result = _resolve_variable_type("list[text]", {})
    assert isinstance(result, ListType)
    assert result.element_type == PrimitiveTypeEnum.text

    # Test different element types
    result = _resolve_variable_type("list[int]", {})
    assert isinstance(result, ListType)
    assert result.element_type == PrimitiveTypeEnum.int

    # Test custom type in list should work (returns string reference)
    result = _resolve_variable_type("list[CustomType]", {})
    assert isinstance(result, ListType)
    assert result.element_type == "CustomType"


def test_list_type_yaml_loading():
    """Test loading YAML with list[type] syntax."""
    yaml_content = """
- id: test_tool
  name: test
  type: APITool
  description: Test tool with list parameters
  endpoint: https://api.example.com/test
  method: POST
  inputs:
    urls:
      type: list[text]
      optional: false
    query:
      type: text
      optional: false
  outputs:
    result:
      type: text
      optional: false
"""

    document, custom_types = load(yaml_content)

    # Document should be a ToolList (RootModel)
    from qtype.semantic.model import ToolList

    assert isinstance(document, ToolList)
    assert len(document.root) == 1
    tool = document.root[0]

    urls_param = tool.inputs["urls"]
    assert isinstance(urls_param.type, ListType)
    assert urls_param.type.element_type == PrimitiveTypeEnum.text
    assert not urls_param.optional


def test_list_type_with_python_functions():
    """Test that list types work with Python function introspection."""
    from qtype.application.converters.tools_from_module import (
        _map_python_type_to_variable_type,
    )
    from qtype.dsl.model import ListType

    # Test list[str] -> ListType
    result = _map_python_type_to_variable_type(list[str], {})
    assert isinstance(result, ListType)
    assert result.element_type == PrimitiveTypeEnum.text

    # Test list[int] -> ListType
    result = _map_python_type_to_variable_type(list[int], {})
    assert isinstance(result, ListType)
    assert result.element_type == PrimitiveTypeEnum.int
