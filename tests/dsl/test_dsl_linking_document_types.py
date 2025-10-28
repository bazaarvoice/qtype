"""
Test DSL linking for all Document types (not just Application).

This module tests that the linker can handle all DocumentType variants:
- Application
- AuthorizationProviderList
- ModelList
- ToolList
- TypeList
- VariableList

Note: Agent, Flow, and IndexList are not standalone document types because
they contain references to external components that cannot be resolved in
isolation (e.g., Agent needs a Model, VectorIndex needs an EmbeddingModel).
"""

from __future__ import annotations

import glob
from pathlib import Path
from typing import Any

import pytest
from pydantic import BaseModel

from qtype import dsl
from qtype.dsl import linker, loader

TEST_DIR = Path(__file__).parent.parent / "document-specs"


def has_reference(obj: Any) -> bool:
    """
    Recursively check if an object contains any Reference instances.

    After linking, there should be no Reference instances left.
    """
    if isinstance(obj, dsl.Reference):
        return True
    if isinstance(obj, BaseModel):
        for _, field_value in obj.__iter__():
            if has_reference(field_value):
                return True
    elif isinstance(obj, list):
        for item in obj:
            if has_reference(item):
                return True
    elif isinstance(obj, dict):
        for item in obj.values():
            if has_reference(item):
                return True
    return False


def run_linking(yaml_path: Path):
    """Load and link a DSL Document from a YAML file."""
    model, dynamic_types_registry = loader.load_document(yaml_path)
    linked_doc = linker.link(model)
    assert not has_reference(linked_doc), (
        "There are unresolved Reference instances"
    )
    return linked_doc


@pytest.mark.parametrize(
    "yaml_file",
    [Path(f).name for f in glob.glob(str(TEST_DIR / "valid_*.qtype.yaml"))],
)
def test_valid_document_types(yaml_file: str) -> None:
    """Test that valid DSL Document YAML files pass linking."""
    yaml_path = TEST_DIR / yaml_file
    # Should not throw an exception
    doc = run_linking(yaml_path)
    assert doc is not None, f"Failed to link {yaml_file}"


@pytest.mark.parametrize(
    "yaml_file,expected_exception",
    [
        (
            "invalid_authorization_provider_list_duplicate_ids.qtype.yaml",
            linker.DuplicateComponentError,
        ),
        (
            "invalid_model_list_duplicate_ids.qtype.yaml",
            linker.DuplicateComponentError,
        ),
        (
            "invalid_tool_list_duplicate_ids.qtype.yaml",
            linker.DuplicateComponentError,
        ),
        (
            "invalid_type_list_duplicate_ids.qtype.yaml",
            linker.DuplicateComponentError,
        ),
        (
            "invalid_variable_list_duplicate_ids.qtype.yaml",
            linker.DuplicateComponentError,
        ),
    ],
)
def test_invalid_document_types(
    yaml_file: str, expected_exception: type[Exception]
) -> None:
    """Test that invalid DSL Document YAML files raise the expected exception."""
    yaml_path = TEST_DIR / yaml_file
    with pytest.raises(expected_exception):
        run_linking(yaml_path)
