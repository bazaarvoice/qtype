"""Test list type functionality in the semantic layer."""

from __future__ import annotations

from pathlib import Path

from qtype.semantic.loader import load


def test_list_type_semantic_conversion():
    """Test that list types work through the full semantic conversion."""
    # Load test YAML file from the same directory
    test_yaml_path = Path(__file__).parent / "test_list_type.qtype.yaml"

    semantic_model, custom_types = load(test_yaml_path)
