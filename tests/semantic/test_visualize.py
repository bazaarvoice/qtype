"""Unit tests for the visualization functionality."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from qtype.semantic.loader import load
from qtype.semantic.model import Application
from qtype.semantic.visualize import visualize_application


def test_visualize_application_with_hello_world_chat():
    """Test that visualize_application produces valid Mermaid output."""
    # Load the DSL example file
    example_path = (
        Path(__file__).parent.parent
        / "specs"
        / "full_application_test.qtype.yaml"
    )
    assert example_path.exists(), f"Example file not found: {example_path}"

    # Load and parse the document
    content = example_path.read_text(encoding="utf-8")
    semantic_app, _ = load(content)

    assert isinstance(semantic_app, Application)

    # Call visualize_application
    mermaid_output = visualize_application(semantic_app)

    # Verify the result is a non-empty string
    assert isinstance(mermaid_output, str)
    assert len(mermaid_output) > 0

    # Test Mermaid validity using mermaid-py library
    try:
        import mermaid as md  # type: ignore[import-untyped]

        # Mock the HTTP requests to avoid SSL issues
        mock_response = Mock()
        mock_response.text = "<svg>mock svg content</svg>"
        with patch("requests.get", return_value=mock_response):
            # This should not raise an exception if the mermaid is valid
            mm = md.Mermaid(mermaid_output)

            # Try to render to HTML (basic validation)
            html_output = mm._repr_html_()
            assert isinstance(html_output, str)
            assert len(html_output) > 0
            assert "svg" in html_output.lower()

    except Exception as e:
        pytest.fail(f"Generated Mermaid diagram is invalid: {e}")
