"""Test list type functionality."""

from qtype.dsl.base_types import PrimitiveTypeEnum
from qtype.dsl.model import ListType, Variable, _resolve_variable_type
from qtype.loader import load_document


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
id: test_list_type

variables:
- id: urls
  type: list[text]
- id: numbers
  type: list[int]

tools:
- id: test_tool
  name: test
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

    document, custom_types = load_document(yaml_content)

    # Check variables
    assert len(document.variables) == 2

    urls_var = next(v for v in document.variables if v.id == "urls")
    assert isinstance(urls_var.type, ListType)
    assert urls_var.type.element_type == PrimitiveTypeEnum.text

    numbers_var = next(v for v in document.variables if v.id == "numbers")
    assert isinstance(numbers_var.type, ListType)
    assert numbers_var.type.element_type == PrimitiveTypeEnum.int

    # Check tool parameters
    assert len(document.tools) == 1
    tool = document.tools[0]

    urls_param = tool.inputs["urls"]
    assert isinstance(urls_param.type, ListType)
    assert urls_param.type.element_type == PrimitiveTypeEnum.text
    assert not urls_param.optional


def test_list_type_semantic_conversion():
    """Test that list types work through the full semantic conversion."""
    import tempfile
    from pathlib import Path

    from qtype.application.facade import QTypeFacade

    yaml_content = """
id: test_semantic_list

variables:
- id: urls
  type: list[text]
- id: result
  type: text

flows:
- id: test_flow
  inputs:
  - urls
  outputs:
  - result
  steps:
  - id: dummy_step
    type: PromptTemplate
    template: "Processing URLs: {urls}"
    inputs:
    - urls
    outputs:
    - result
"""

    # Create temporary file for testing
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".qtype.yaml", delete=False
    ) as f:
        f.write(yaml_content)
        temp_path = f.name

    try:
        facade = QTypeFacade()
        semantic_model, custom_types = facade.load_semantic_model(
            Path(temp_path)
        )

        # Check that semantic variable has correct list type
        urls_var = next(v for v in semantic_model.variables if v.id == "urls")
        from qtype.semantic.model import ListType as SemanticListType

        assert isinstance(urls_var.type, SemanticListType)
        assert urls_var.type.element_type == PrimitiveTypeEnum.text
    finally:
        # Clean up temporary file
        Path(temp_path).unlink()


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
