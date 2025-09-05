"""Main facade for qtype operations."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from qtype.base.exceptions import LoadError, ValidationError
from qtype.base.logging import get_logger
from qtype.base.types import PathLike
from qtype.dsl.model import Application as DSLApplication
from qtype.dsl.model import Document
from qtype.semantic.model import Application as SemanticApplication

from .services import (
    ConversionService,
    ExecutionService,
    GenerationService,
    LoadingService,
    ValidationService,
    VisualizationService,
)

logger = get_logger("application.facade")


class QTypeFacade:
    """
    Simplified interface for all qtype operations.

    This facade hides the complexity of coordinating between DSL, semantic,
    and interpreter layers, providing a clean API for common operations.
    """

    def __init__(self) -> None:
        """Initialize the facade with all necessary services."""
        self._loading_service = LoadingService()
        self._validation_service = ValidationService()
        self._conversion_service = ConversionService()
        self._generation_service = GenerationService()
        self._visualization_service = VisualizationService()
        self._execution_service = ExecutionService()

    def load_and_validate(self, path: PathLike) -> DSLApplication:
        """
        Load and validate a document in one operation.

        This is the most common operation - combines loading, parsing,
        semantic resolution, and validation.

        Args:
            path: Path to the qtype document

        Returns:
            The validated DSL application

        Raises:
            LoadError: If loading fails
            ValidationError: If validation fails
        """
        try:
            path_obj = Path(path)
            logger.info(f"Loading and validating document: {path_obj}")

            # Load the DSL document
            document = self._loading_service.load_document_dsl_only(path_obj)

            # Validate it
            errors = self._validation_service.validate_document(document)
            if errors:
                raise ValidationError(
                    f"Validation failed: {'; '.join(errors)}", errors
                )

            logger.info("Document loaded and validated successfully")
            return document

        except (LoadError, ValidationError):
            raise
        except Exception as e:
            raise LoadError(f"Failed to load/validate {path}: {e}") from e

    def load_semantic_model(self, path: PathLike) -> SemanticApplication:
        """
        Load a document and return the resolved semantic model.

        Args:
            path: Path to the qtype document

        Returns:
            The resolved semantic application model

        Raises:
            LoadError: If loading fails
            ValidationError: If resolution fails
        """
        try:
            path_obj = Path(path)
            logger.info(f"Loading semantic model: {path_obj}")

            semantic_model, _ = self._loading_service.load_document(path_obj)
            return semantic_model

        except Exception as e:
            raise LoadError(
                f"Failed to load semantic model from {path}: {e}"
            ) from e

    def execute_workflow(
        self,
        path: PathLike,
        flow_name: str | None = None,
        **kwargs: Any,
    ) -> Any:
        """
        Execute a complete workflow from document to results.

        This orchestrates the entire pipeline: Load -> Validate -> Execute

        Args:
            path: Path to the qtype document
            flow_name: Name of the flow to execute (optional)
            **kwargs: Input variables for the workflow

        Returns:
            The workflow execution results

        Raises:
            LoadError: If loading fails
            ValidationError: If validation fails
            InterpreterError: If execution fails
        """
        try:
            logger.info(f"Executing workflow from {path}")

            # Load and validate document
            document = self.load_and_validate(path)

            # Execute the workflow
            return self._execution_service.execute_workflow(
                document, flow_name, **kwargs
            )

        except Exception as e:
            from qtype.base.exceptions import InterpreterError

            if isinstance(e, (LoadError, ValidationError)):
                raise
            raise InterpreterError(f"Workflow execution failed: {e}") from e

    def validate_only(self, path: PathLike) -> list[str]:
        """
        Validate a document and return any errors.

        Args:
            path: Path to the qtype document

        Returns:
            List of validation error messages (empty if valid)

        Raises:
            LoadError: If loading fails
        """
        try:
            path_obj = Path(path)
            document = self._loading_service.load_document_dsl_only(path_obj)
            return self._validation_service.validate_document(document)

        except Exception as e:
            raise LoadError(f"Failed to validate {path}: {e}") from e

    def convert_to_format(self, path: PathLike, target_format: str) -> str:
        """
        Convert document to different formats.

        Args:
            path: Path to the qtype document
            target_format: Target format ('yaml' only)

        Returns:
            The converted document as a string

        Raises:
            LoadError: If loading fails
            ValueError: If format is not supported
        """
        try:
            document = self.load_and_validate(path)

            if target_format.lower() == "yaml":
                # Wrap Application in Document for conversion
                doc = Document(root=document)
                return self._conversion_service.convert_to_yaml(doc)
            else:
                raise ValueError(f"Unsupported format: {target_format}")

        except Exception as e:
            if isinstance(e, (LoadError, ValidationError, ValueError)):
                raise
            raise LoadError(
                f"Failed to convert {path} to {target_format}: {e}"
            ) from e

    def generate_schema(self, path: PathLike) -> dict[str, Any]:
        """
        Generate JSON schema from qtype document.

        Args:
            path: Path to the qtype document

        Returns:
            The generated JSON schema

        Raises:
            LoadError: If loading fails
            ValidationError: If schema generation fails
        """
        try:
            document = self.load_and_validate(path)
            return self._generation_service.generate_schema(document)

        except Exception as e:
            if isinstance(e, (LoadError, ValidationError)):
                raise
            raise ValidationError(
                f"Failed to generate schema for {path}: {e}"
            ) from e

    def visualize_application(self, path: PathLike) -> str:
        """
        Generate visualization of the application structure.

        Args:
            path: Path to the qtype document

        Returns:
            The visualization as a string (e.g., Mermaid diagram)

        Raises:
            LoadError: If loading fails
            ValidationError: If visualization generation fails
        """
        try:
            document = self.load_and_validate(path)
            return self._visualization_service.visualize_application(document)

        except Exception as e:
            if isinstance(e, (LoadError, ValidationError)):
                raise
            raise ValidationError(f"Failed to visualize {path}: {e}") from e

    # Convenience methods for working with loaded documents

    def validate_document(self, document: DSLApplication) -> list[str]:
        """Validate an already-loaded document."""
        return self._validation_service.validate_document(document)

    def execute_document_workflow(
        self,
        document: DSLApplication,
        flow_name: str | None = None,
        **kwargs: Any,
    ) -> Any:
        """Execute a workflow from an already-loaded document."""
        return self._execution_service.execute_workflow(
            document, flow_name, **kwargs
        )

    def convert_document(self, document: Document | DSLApplication) -> str:
        """Convert a document to YAML format."""
        # If it's an Application, wrap it in a Document
        if isinstance(document, DSLApplication):
            doc = Document(root=document)
        else:
            doc = document
        return self._conversion_service.convert_to_yaml(doc)
