"""Test list type functionality in the semantic layer."""

from __future__ import annotations

from pathlib import Path

from qtype.application.facade import QTypeFacade
from qtype.base.types import PrimitiveTypeEnum
from qtype.semantic.model import Application
from qtype.semantic.model import ListType as SemanticListType


def test_list_type_semantic_conversion():
    """Test that list types work through the full semantic conversion."""
    # Load test YAML file from the same directory
    test_yaml_path = Path(__file__).parent / "test_list_type.qtype.yaml"

    facade = QTypeFacade()
    semantic_model, custom_types = facade.load_semantic_model(test_yaml_path)
    assert isinstance(semantic_model, Application)

    # Check that semantic variable has correct list type
    urls_var = next(
        v for v in semantic_model.flows[0].inputs if v.id == "urls"
    )
    assert isinstance(urls_var.type, SemanticListType)
    assert urls_var.type.element_type == PrimitiveTypeEnum.text
