"""Unit tests for the application facade.

These tests focus on the facade's coordination logic, error handling,
and service orchestration. They do NOT test the business logic within
the services - that should be tested separately.
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import Mock

import pytest

from qtype.base.exceptions import InterpreterError, LoadError, ValidationError
from qtype.dsl.model import Application as DSLApplication
from qtype.semantic.model import Application as SemanticApplication


class TestQTypeFacade:
    """Test the QTypeFacade coordination and error handling."""

    @pytest.fixture
    def facade_with_mocks(self):
        """Create a facade instance with mocked services."""
        from qtype.application.facade import QTypeFacade

        facade = QTypeFacade()

        # Mock all the services directly on the facade instance
        facade._loading_service = Mock()
        facade._validation_service = Mock()
        facade._conversion_service = Mock()
        facade._generation_service = Mock()
        facade._visualization_service = Mock()
        facade._execution_service = Mock()

        return facade

    @pytest.fixture
    def mock_dsl_app(self):
        """Create a mock DSL application."""
        return Mock(spec=DSLApplication)

    @pytest.fixture
    def mock_semantic_app(self):
        """Create a mock semantic application."""
        return Mock(spec=SemanticApplication)

    @pytest.fixture
    def sample_path(self):
        """Create a sample path for testing."""
        return Path("/test/sample.qtype.yaml")

    def test_load_and_validate_success(
        self, facade_with_mocks, mock_dsl_app, sample_path
    ):
        """Test successful load and validate coordination."""
        # Arrange
        facade_with_mocks._loading_service.load_document_dsl_only.return_value = mock_dsl_app
        facade_with_mocks._validation_service.validate_document.return_value = []  # No errors

        # Act
        result = facade_with_mocks.load_and_validate(sample_path)

        # Assert - verify coordination logic
        facade_with_mocks._loading_service.load_document_dsl_only.assert_called_once_with(
            sample_path
        )
        facade_with_mocks._validation_service.validate_document.assert_called_once_with(
            mock_dsl_app
        )
        assert result == mock_dsl_app

    def test_load_and_validate_with_validation_errors(
        self, facade_with_mocks, mock_dsl_app, sample_path
    ):
        """Test load and validate handles validation errors correctly."""
        # Arrange
        facade_with_mocks._loading_service.load_document_dsl_only.return_value = mock_dsl_app
        facade_with_mocks._validation_service.validate_document.return_value = [
            "Error 1",
            "Error 2",
        ]

        # Act & Assert
        with pytest.raises(
            ValidationError, match="Validation failed: Error 1; Error 2"
        ):
            facade_with_mocks.load_and_validate(sample_path)

        # Verify services were called correctly
        facade_with_mocks._loading_service.load_document_dsl_only.assert_called_once_with(
            sample_path
        )
        facade_with_mocks._validation_service.validate_document.assert_called_once_with(
            mock_dsl_app
        )

    def test_load_and_validate_handles_load_error(
        self, facade_with_mocks, sample_path
    ):
        """Test load and validate propagates load errors."""
        # Arrange
        facade_with_mocks._loading_service.load_document_dsl_only.side_effect = LoadError(
            "Load failed"
        )

        # Act & Assert
        with pytest.raises(LoadError, match="Load failed"):
            facade_with_mocks.load_and_validate(sample_path)

        facade_with_mocks._loading_service.load_document_dsl_only.assert_called_once_with(
            sample_path
        )
        facade_with_mocks._validation_service.validate_document.assert_not_called()

    def test_load_and_validate_handles_unexpected_error(
        self, facade_with_mocks, sample_path
    ):
        """Test load and validate wraps unexpected errors as LoadError."""
        # Arrange
        facade_with_mocks._loading_service.load_document_dsl_only.side_effect = ValueError(
            "Unexpected error"
        )

        # Act & Assert
        with pytest.raises(
            LoadError, match="Failed to load/validate.*Unexpected error"
        ):
            facade_with_mocks.load_and_validate(sample_path)

    def test_load_semantic_model_success(
        self, facade_with_mocks, mock_semantic_app, sample_path
    ):
        """Test successful semantic model loading."""
        # Arrange
        facade_with_mocks._loading_service.load_document.return_value = (
            mock_semantic_app,
            None,
        )

        # Act
        result = facade_with_mocks.load_semantic_model(sample_path)

        # Assert
        facade_with_mocks._loading_service.load_document.assert_called_once_with(
            sample_path
        )
        assert result == mock_semantic_app

    def test_load_semantic_model_handles_error(
        self, facade_with_mocks, sample_path
    ):
        """Test semantic model loading handles errors."""
        # Arrange
        facade_with_mocks._loading_service.load_document.side_effect = (
            Exception("Load failed")
        )

        # Act & Assert
        with pytest.raises(
            LoadError, match="Failed to load semantic model.*Load failed"
        ):
            facade_with_mocks.load_semantic_model(sample_path)

    def test_execute_workflow_success(
        self, facade_with_mocks, mock_dsl_app, sample_path
    ):
        """Test successful workflow execution coordination."""
        # Arrange
        facade_with_mocks._loading_service.load_document_dsl_only.return_value = mock_dsl_app
        facade_with_mocks._validation_service.validate_document.return_value = []
        facade_with_mocks._execution_service.execute_workflow.return_value = {
            "result": "success"
        }

        # Act
        result = facade_with_mocks.execute_workflow(
            sample_path, "test_flow", input1="value1"
        )

        # Assert - verify coordination
        facade_with_mocks._loading_service.load_document_dsl_only.assert_called_once_with(
            sample_path
        )
        facade_with_mocks._validation_service.validate_document.assert_called_once_with(
            mock_dsl_app
        )
        facade_with_mocks._execution_service.execute_workflow.assert_called_once_with(
            mock_dsl_app, "test_flow", input1="value1"
        )
        assert result == {"result": "success"}

    def test_execute_workflow_propagates_load_and_validation_errors(
        self, facade_with_mocks, sample_path
    ):
        """Test workflow execution propagates load/validation errors correctly."""
        # Test LoadError propagation
        facade_with_mocks._loading_service.load_document_dsl_only.side_effect = LoadError(
            "Load failed"
        )

        with pytest.raises(LoadError, match="Load failed"):
            facade_with_mocks.execute_workflow(sample_path)

        # Test ValidationError propagation (reset the mock first)
        facade_with_mocks._loading_service.load_document_dsl_only.side_effect = None
        facade_with_mocks._loading_service.load_document_dsl_only.return_value = Mock()
        facade_with_mocks._validation_service.validate_document.return_value = [
            "Validation error"
        ]

        with pytest.raises(ValidationError):
            facade_with_mocks.execute_workflow(sample_path)

    def test_execute_workflow_wraps_execution_error(
        self, facade_with_mocks, mock_dsl_app, sample_path
    ):
        """Test workflow execution wraps execution errors as InterpreterError."""
        # Arrange
        facade_with_mocks._loading_service.load_document_dsl_only.return_value = mock_dsl_app
        facade_with_mocks._validation_service.validate_document.return_value = []
        facade_with_mocks._execution_service.execute_workflow.side_effect = (
            Exception("Execution failed")
        )

        # Act & Assert
        with pytest.raises(
            InterpreterError,
            match="Workflow execution failed.*Execution failed",
        ):
            facade_with_mocks.execute_workflow(sample_path)

    def test_validate_only_success(
        self, facade_with_mocks, mock_dsl_app, sample_path
    ):
        """Test validate-only operation returns errors correctly."""
        # Arrange
        facade_with_mocks._loading_service.load_document_dsl_only.return_value = mock_dsl_app
        facade_with_mocks._validation_service.validate_document.return_value = [
            "Error 1"
        ]

        # Act
        result = facade_with_mocks.validate_only(sample_path)

        # Assert
        facade_with_mocks._loading_service.load_document_dsl_only.assert_called_once_with(
            sample_path
        )
        facade_with_mocks._validation_service.validate_document.assert_called_once_with(
            mock_dsl_app
        )
        assert result == ["Error 1"]

    def test_validate_only_handles_load_error(
        self, facade_with_mocks, sample_path
    ):
        """Test validate-only operation handles load errors."""
        # Arrange
        facade_with_mocks._loading_service.load_document_dsl_only.side_effect = Exception(
            "Load failed"
        )

        # Act & Assert
        with pytest.raises(LoadError, match="Failed to validate.*Load failed"):
            facade_with_mocks.validate_only(sample_path)

    def test_generate_schema_success(
        self, facade_with_mocks, mock_dsl_app, sample_path
    ):
        """Test successful schema generation coordination."""
        # Arrange
        facade_with_mocks._loading_service.load_document_dsl_only.return_value = mock_dsl_app
        facade_with_mocks._validation_service.validate_document.return_value = []
        facade_with_mocks._generation_service.generate_schema.return_value = {
            "schema": "data"
        }

        # Act
        result = facade_with_mocks.generate_schema(sample_path)

        # Assert
        facade_with_mocks._loading_service.load_document_dsl_only.assert_called_once_with(
            sample_path
        )
        facade_with_mocks._validation_service.validate_document.assert_called_once_with(
            mock_dsl_app
        )
        facade_with_mocks._generation_service.generate_schema.assert_called_once_with(
            mock_dsl_app
        )
        assert result == {"schema": "data"}

    def test_generate_schema_propagates_load_validation_errors(
        self, facade_with_mocks, sample_path
    ):
        """Test schema generation propagates load/validation errors."""
        # Test LoadError propagation
        facade_with_mocks._loading_service.load_document_dsl_only.side_effect = LoadError(
            "Load failed"
        )

        with pytest.raises(LoadError, match="Load failed"):
            facade_with_mocks.generate_schema(sample_path)

    def test_generate_schema_wraps_generation_error(
        self, facade_with_mocks, mock_dsl_app, sample_path
    ):
        """Test schema generation wraps generation errors as ValidationError."""
        # Arrange
        facade_with_mocks._loading_service.load_document_dsl_only.return_value = mock_dsl_app
        facade_with_mocks._validation_service.validate_document.return_value = []
        facade_with_mocks._generation_service.generate_schema.side_effect = (
            Exception("Generation failed")
        )

        # Act & Assert
        with pytest.raises(
            ValidationError,
            match="Failed to generate schema.*Generation failed",
        ):
            facade_with_mocks.generate_schema(sample_path)

    def test_visualize_application_success(
        self, facade_with_mocks, mock_dsl_app, sample_path
    ):
        """Test successful visualization coordination."""
        # Arrange
        facade_with_mocks._loading_service.load_document_dsl_only.return_value = mock_dsl_app
        facade_with_mocks._validation_service.validate_document.return_value = []
        facade_with_mocks._visualization_service.visualize_application.return_value = "mermaid diagram"

        # Act
        result = facade_with_mocks.visualize_application(sample_path)

        # Assert
        facade_with_mocks._loading_service.load_document_dsl_only.assert_called_once_with(
            sample_path
        )
        facade_with_mocks._validation_service.validate_document.assert_called_once_with(
            mock_dsl_app
        )
        facade_with_mocks._visualization_service.visualize_application.assert_called_once_with(
            mock_dsl_app
        )
        assert result == "mermaid diagram"

    def test_visualize_application_wraps_visualization_error(
        self, facade_with_mocks, mock_dsl_app, sample_path
    ):
        """Test visualization wraps visualization errors as ValidationError."""
        # Arrange
        facade_with_mocks._loading_service.load_document_dsl_only.return_value = mock_dsl_app
        facade_with_mocks._validation_service.validate_document.return_value = []
        facade_with_mocks._visualization_service.visualize_application.side_effect = Exception(
            "Viz failed"
        )

        # Act & Assert
        with pytest.raises(
            ValidationError, match="Failed to visualize.*Viz failed"
        ):
            facade_with_mocks.visualize_application(sample_path)

    def test_validate_document_delegates_correctly(
        self, facade_with_mocks, mock_dsl_app
    ):
        """Test validate_document convenience method delegates correctly."""
        # Arrange
        facade_with_mocks._validation_service.validate_document.return_value = [
            "Error"
        ]

        # Act
        result = facade_with_mocks.validate_document(mock_dsl_app)

        # Assert
        facade_with_mocks._validation_service.validate_document.assert_called_once_with(
            mock_dsl_app
        )
        assert result == ["Error"]

    def test_execute_document_workflow_delegates_correctly(
        self, facade_with_mocks, mock_dsl_app
    ):
        """Test execute_document_workflow convenience method delegates correctly."""
        # Arrange
        facade_with_mocks._execution_service.execute_workflow.return_value = {
            "result": "success"
        }

        # Act
        result = facade_with_mocks.execute_document_workflow(
            mock_dsl_app, "flow_name", input1="value1"
        )

        # Assert
        facade_with_mocks._execution_service.execute_workflow.assert_called_once_with(
            mock_dsl_app, "flow_name", input1="value1"
        )
        assert result == {"result": "success"}

    def test_convert_document_delegates_correctly(self, facade_with_mocks):
        """Test convert_document convenience method delegates correctly."""
        # Arrange
        mock_document = Mock()
        facade_with_mocks._conversion_service.convert_to_yaml.return_value = (
            "yaml output"
        )

        # Act
        result = facade_with_mocks.convert_document(mock_document)

        # Assert
        facade_with_mocks._conversion_service.convert_to_yaml.assert_called_once_with(
            mock_document
        )
        assert result == "yaml output"

    def test_path_conversion_to_pathlib(self, facade_with_mocks, mock_dsl_app):
        """Test that string paths are properly converted to Path objects."""
        # Arrange
        facade_with_mocks._loading_service.load_document_dsl_only.return_value = mock_dsl_app
        facade_with_mocks._validation_service.validate_document.return_value = []

        # Act
        facade_with_mocks.load_and_validate("/test/path.yaml")  # String path

        # Assert - verify Path object was passed to service
        call_args = facade_with_mocks._loading_service.load_document_dsl_only.call_args[
            0
        ][0]
        assert isinstance(call_args, Path)
        assert str(call_args) == "/test/path.yaml"
