"""Main facade for qtype operations."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from qtype.base.exceptions import InterpreterError, LoadError, ValidationError
from qtype.base.logging import get_logger
from qtype.base.types import PathLike
from qtype.dsl.model import Application as DSLApplication
from qtype.dsl.model import DocumentType
from qtype.semantic.model import Application as SemanticApplication

logger = get_logger("application.facade")


class QTypeFacade:
    """
    Simplified interface for all qtype operations.

    This facade hides the complexity of coordinating between DSL, semantic,
    and interpreter layers, providing a clean API for common operations.
    """

    def __init__(self) -> None:
        """Initialize the facade."""
        # Lazy-loaded imports to avoid circular dependencies
        self._loader = None
        self._resolver = None
        self._validator = None

    def _validate_loaded_document(self, document: DSLApplication) -> list[str]:
        """Helper method to validate an already-loaded DSL document."""
        logger.info("Validating document")
        errors: list[str] = []

        # DSL-level validation
        if self._validator is None:
            from qtype.dsl.validator import validate

            self._validator = validate

        try:
            self._validator(document)
        except Exception as e:
            errors.append(f"DSL validation failed: {e}")

        # Semantic-level validation
        if self._resolver is None:
            from qtype.semantic.resolver import resolve

            self._resolver = resolve

        try:
            self._resolver(document)
        except Exception as e:
            errors.append(f"Semantic validation failed: {e}")

        if errors:
            logger.warning(f"Validation failed with {len(errors)} errors")
        else:
            logger.info("Document validation passed")

        return errors

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
            from qtype.loader import load_document

            content = path_obj.read_text(encoding="utf-8")
            dsl_app, _ = load_document(content)
            if not isinstance(dsl_app, DSLApplication):
                raise ValueError(
                    f"Root document is not an Application, found {type(dsl_app)}"
                )

            # Validate the document
            errors = self._validate_loaded_document(dsl_app)
            if errors:
                raise ValidationError(
                    f"Validation failed: {'; '.join(errors)}", errors
                )

            logger.info("Document loaded and validated successfully")
            return dsl_app

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

            # Load the document
            if self._loader is None:
                from qtype.loader import load

                self._loader = load

            content = path_obj.read_text(encoding="utf-8")
            semantic_model, _ = self._loader(content)
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
            if self._resolver is None:
                from qtype.semantic.resolver import resolve

                self._resolver = resolve

            logger.info(f"Executing workflow: {flow_name or 'default'}")
            semantic_model = self._resolver(document)

            # Find the flow to execute
            target_flow = None
            if flow_name:
                for flow in semantic_model.flows:
                    if flow.id == flow_name:
                        target_flow = flow
                        break
                if target_flow is None:
                    raise ValueError(f"Flow '{flow_name}' not found")
            else:
                if semantic_model.flows:
                    target_flow = semantic_model.flows[0]
                else:
                    raise ValueError("No flows found in application")

            from qtype.interpreter.flow import execute_flow

            return execute_flow(target_flow, **kwargs)

        except Exception as e:
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

            # Load the DSL document
            from qtype.loader import load_document

            content = path_obj.read_text(encoding="utf-8")
            dsl_app, _ = load_document(content)
            if not isinstance(dsl_app, DSLApplication):
                raise ValueError(
                    f"Root document is not an Application, found {type(dsl_app)}"
                )

            # Validate the document
            return self._validate_loaded_document(dsl_app)

        except Exception as e:
            raise LoadError(f"Failed to validate {path}: {e}") from e

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

            # Generate schema from the semantic model
            if self._resolver is None:
                from qtype.semantic.resolver import resolve

                self._resolver = resolve

            semantic_model = self._resolver(document)

            # For now, return the schema of the semantic model
            # TODO: Implement proper schema generation
            return semantic_model.model_json_schema()

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

            # Generate visualization from the semantic model
            if self._resolver is None:
                from qtype.semantic.resolver import resolve

                self._resolver = resolve

            semantic_model = self._resolver(document)

            from qtype.semantic.visualize import visualize_application

            return visualize_application(semantic_model)

        except Exception as e:
            if isinstance(e, (LoadError, ValidationError)):
                raise
            raise ValidationError(f"Failed to visualize {path}: {e}") from e

    # Convenience methods for working with loaded documents

    def validate_document(self, document: DSLApplication) -> list[str]:
        """Validate an already-loaded document."""
        return self._validate_loaded_document(document)

    def execute_document_workflow(
        self,
        document: DSLApplication,
        flow_name: str | None = None,
        **kwargs: Any,
    ) -> Any:
        """Execute a workflow from an already-loaded document."""
        try:
            if self._resolver is None:
                from qtype.semantic.resolver import resolve

                self._resolver = resolve

            logger.info(f"Executing workflow: {flow_name or 'default'}")
            semantic_model = self._resolver(document)

            # Find the flow to execute
            target_flow = None
            if flow_name:
                for flow in semantic_model.flows:
                    if flow.id == flow_name:
                        target_flow = flow
                        break
                if target_flow is None:
                    raise ValueError(f"Flow '{flow_name}' not found")
            else:
                if semantic_model.flows:
                    target_flow = semantic_model.flows[0]
                else:
                    raise ValueError("No flows found in application")

            from qtype.interpreter.flow import execute_flow

            return execute_flow(target_flow, **kwargs)

        except Exception as e:
            raise InterpreterError(f"Workflow execution failed: {e}") from e

    def convert_document(self, document: DocumentType) -> str:
        """Convert a document to YAML format."""
        try:
            from pydantic_yaml import to_yaml_str

            # If it's an Application, wrap it in a Document
            if isinstance(document, DSLApplication):
                from qtype.dsl.model import Document

                wrapped_document = Document(root=document)
                return to_yaml_str(
                    wrapped_document, exclude_unset=True, exclude_none=True
                )

            return to_yaml_str(document, exclude_unset=True, exclude_none=True)
        except ImportError:
            # Fallback to basic YAML if pydantic_yaml is not available
            import yaml

            if isinstance(document, DSLApplication):
                from qtype.dsl.model import Document

                wrapped_document = Document(root=document)
                document_dict = wrapped_document.model_dump(
                    exclude_unset=True, exclude_none=True
                )
            else:
                document_dict = document.model_dump(
                    exclude_unset=True, exclude_none=True
                )

            return yaml.dump(document_dict, default_flow_style=False)

    def generate_aws_bedrock_models(self) -> list[dict[str, Any]]:
        """
        Generate AWS Bedrock model definitions.

        Returns:
            List of model definitions for AWS Bedrock models.

        Raises:
            ImportError: If boto3 is not installed.
            Exception: If AWS API call fails.
        """
        try:
            import boto3

            logger.info("Discovering AWS Bedrock models...")
            client = boto3.client("bedrock")
            models = client.list_foundation_models()

            model_definitions = []
            for model_summary in models.get("modelSummaries", []):
                model_definitions.append(
                    {
                        "id": model_summary["modelId"],
                        "provider": "aws-bedrock",
                    }
                )

            logger.info(
                f"Discovered {len(model_definitions)} AWS Bedrock models"
            )
            return model_definitions

        except ImportError as e:
            logger.error(
                "boto3 is not installed. Please install it to use AWS Bedrock model discovery."
            )
            raise ImportError(
                "boto3 is required for AWS Bedrock model discovery"
            ) from e

        except Exception as e:
            logger.error(f"Failed to discover AWS Bedrock models: {e}")
            raise
