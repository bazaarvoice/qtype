"""
Test semantic resolver and checker for all Document types.

This module tests that the semantic resolver and checker can handle all
DocumentType variants, not just Application.
"""

from __future__ import annotations

import glob
from pathlib import Path

import pytest

from qtype.semantic import model as ir
from qtype.semantic.loader import load_from_string

TEST_DIR = Path(__file__).parent.parent / "document-specs"


@pytest.mark.parametrize(
    "yaml_file",
    [Path(f).name for f in glob.glob(str(TEST_DIR / "valid_*.qtype.yaml"))],
)
def test_resolve_and_check_all_document_types(yaml_file: str) -> None:
    """Test that all valid DocumentType YAMLs can be resolved and checked."""
    yaml_path = TEST_DIR / yaml_file

    # Load and link the document

    ir_doc, _ = load_from_string(
        yaml_path.read_text(encoding="utf-8"), base_path=yaml_path.parent
    )
    assert ir_doc is not None, f"Failed to resolve {yaml_file}"

    # Verify the IR document is one of the valid DocumentType variants
    assert isinstance(
        ir_doc,
        (
            ir.Application,
            ir.AuthorizationProviderList,
            ir.ModelList,
            ir.ToolList,
            ir.TypeList,
            ir.VariableList,
        ),
    ), f"Expected DocumentType, got {type(ir_doc).__name__}"


def test_resolve_model_list() -> None:
    """Test resolving a ModelList document specifically."""
    yaml_path = TEST_DIR / "valid_model_list.qtype.yaml"

    ir_doc, _ = load_from_string(
        yaml_path.read_text(encoding="utf-8"), base_path=yaml_path.parent
    )

    assert isinstance(ir_doc, ir.ModelList), "Document should be ModelList"
    assert len(ir_doc.root) == 2, "Should have 2 models"
    assert isinstance(ir_doc.root[0], ir.Model), "First should be Model"
    assert isinstance(ir_doc.root[1], ir.EmbeddingModel), (
        "Second should be EmbeddingModel"
    )


def test_resolve_variable_list() -> None:
    """Test resolving a VariableList document specifically."""
    yaml_path = TEST_DIR / "valid_variable_list.qtype.yaml"

    ir_doc, _ = load_from_string(
        yaml_path.read_text(encoding="utf-8"), base_path=yaml_path.parent
    )

    assert isinstance(ir_doc, ir.VariableList), (
        "Document should be VariableList"
    )
    assert len(ir_doc.root) == 4, "Should have 4 variables"
    assert all(isinstance(var, ir.Variable) for var in ir_doc.root), (
        "All items should be Variables"
    )


def test_resolve_authorization_provider_list() -> None:
    """Test resolving an AuthorizationProviderList document specifically."""
    yaml_path = TEST_DIR / "valid_authorization_provider_list.qtype.yaml"

    ir_doc, _ = load_from_string(
        yaml_path.read_text(encoding="utf-8"), base_path=yaml_path.parent
    )

    assert isinstance(ir_doc, ir.AuthorizationProviderList), (
        "Document should be AuthorizationProviderList"
    )
    assert len(ir_doc.root) == 3, "Should have 3 auth providers"
