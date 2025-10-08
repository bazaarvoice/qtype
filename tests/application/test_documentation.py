"""Unit tests for documentation generation functionality."""

import tempfile
from pathlib import Path

from qtype.application.documentation import generate_documentation


def test_generate_documentation_creates_expected_files():
    """Test that generate_documentation creates the expected markdown files."""
    with tempfile.TemporaryDirectory() as temp_dir:
        output_path = Path(temp_dir)

        # Generate documentation
        generate_documentation(output_path)

        # Get all markdown files created
        md_files = list(output_path.glob("*.md"))

        # Verify that files were created
        assert len(md_files) > 0, "No documentation files were generated"

        # Verify some expected files exist (these are core DSL classes)
        expected_files = ["PrimitiveTypeEnum.md"]
        for expected_file in expected_files:
            assert (output_path / expected_file).exists(), (
                f"Expected file {expected_file} not found"
            )

        # Verify all files have content
        for md_file in md_files:
            content = md_file.read_text()
            assert len(content) > 0, f"File {md_file.name} is empty"
            assert "###" in content, (
                f"File {md_file.name} doesn't contain expected markdown headers"
            )
