"""Test list type functionality in the semantic layer."""

from __future__ import annotations

import tempfile
from pathlib import Path

from qtype.application.facade import QTypeFacade
from qtype.dsl.base_types import PrimitiveTypeEnum
from qtype.semantic.model import ListType as SemanticListType


def test_list_type_semantic_conversion():
    """Test that list types work through the full semantic conversion."""
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
        assert isinstance(urls_var.type, SemanticListType)
        assert urls_var.type.element_type == PrimitiveTypeEnum.text
    finally:
        # Clean up temporary file
        Path(temp_path).unlink()
