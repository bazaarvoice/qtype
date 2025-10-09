"""
Unit tests for reference resolution in DSL models.

This module tests that string references (e.g., "my_auth_id") are properly
resolved to Reference[T] objects by the normalize_string_references validator
in StrictBaseModel.

Each test loads a YAML spec file that uses string references and verifies
that the loaded model has Reference objects instead of strings.
"""

from __future__ import annotations

from pathlib import Path

from qtype import dsl, loader
from qtype.dsl.base_types import Reference

# Path to the reference test specs
REFERENCE_SPECS_DIR = Path(__file__).parent / "reference_specs"


def load_test_spec(spec_filename: str) -> dsl.Application:
    """
    Load a test spec YAML file and parse it into a DSL Application.

    Args:
        spec_filename: Name of the YAML file in the reference_specs directory

    Returns:
        The parsed DSL Application model (before validation/resolution)
    """
    spec_path = REFERENCE_SPECS_DIR / spec_filename
    yaml_content = spec_path.read_text(encoding="utf-8")

    # Use the loader's load_document function which handles all the parsing
    root, _ = loader.load_document(yaml_content)

    if not isinstance(root, dsl.Application):
        raise TypeError(f"Expected Application, got {type(root)}")

    return root


class TestModelReferenceResolution:
    """Test reference resolution for the Model class."""

    def test_model_auth_string_resolved_to_reference(self) -> None:
        """
        Test that Model.auth field containing a string ID is resolved
        to a Reference[AuthProviderType] object.

        The YAML contains:
            auth: test_auth

        After parsing, it should be:
            auth: Reference(ref="test_auth")
        """
        app = load_test_spec("model_auth_reference.qtype.yaml")

        # Get the model from the application
        assert app.models is not None
        assert len(app.models) == 1
        model = app.models[0]

        # Verify the model has the expected ID
        assert model.id == "test_model"

        # The critical assertion: auth should be a Reference object, not a string
        assert model.auth is not None
        assert isinstance(model.auth, Reference), (
            f"Expected model.auth to be a Reference object, "
            f"but got {type(model.auth).__name__}: {model.auth}"
        )

        # Verify the reference points to the correct auth provider
        assert model.auth.ref == "test_auth"
