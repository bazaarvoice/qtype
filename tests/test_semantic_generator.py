"""Unit tests for semantic model generation functionality."""

import argparse
import ast
import tempfile
from pathlib import Path

from qtype.semantic.generate import generate_semantic_model


def normalize_python_code(code: str) -> str:
    """Normalize Python code by parsing and reformatting it consistently."""
    try:
        # Parse the code into an AST and then dump it back
        # This normalizes formatting differences like import styles
        tree = ast.parse(code)
        return ast.unparse(tree)
    except Exception:
        # If parsing fails, return the original code
        return code


def test_generate_semantic_model_matches_existing():
    """Test that generate_semantic_model produces functionally equivalent output to the existing semantic model."""
    with tempfile.TemporaryDirectory(dir=".") as temp_dir:
        # Create output path for generated file
        output_file = Path(temp_dir) / "generated_model.py"

        # Create args namespace as expected by the function
        args = argparse.Namespace(output=str(output_file))

        # Generate the semantic model
        generate_semantic_model(args)

        # Verify the file was created
        assert output_file.exists(), (
            "Generated semantic model file was not created"
        )

        # Read the generated content
        generated_content = output_file.read_text()

        # Read the existing semantic model content
        existing_model_path = (
            Path(__file__).parent.parent / "qtype" / "semantic" / "model.py"
        )
        assert existing_model_path.exists(), (
            "Existing semantic model file not found"
        )
        existing_content = existing_model_path.read_text()

        # Normalize both pieces of code for comparison
        normalized_generated = normalize_python_code(generated_content)
        normalized_existing = normalize_python_code(existing_content)

        # Compare the normalized contents
        assert normalized_generated == normalized_existing, (
            "Generated semantic model does not functionally match existing model.py. "
            f"Generated file: {output_file}, "
            f"Existing file: {existing_model_path}"
        )

        # Verify the generated file has substantial content
        assert len(generated_content) > 1000, (
            "Generated semantic model appears to be too small"
        )

        # Verify it contains expected imports and classes
        assert "from pydantic import BaseModel" in generated_content
        assert "class Variable(" in generated_content
        assert (
            "Semantic Intermediate Representation models" in generated_content
        )
