"""Main facade for qtype operations."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from qtype.base.exceptions import ValidationError
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
        pass

    def _read_file_content(self, path: PathLike) -> str:
        """Read content from a file path."""
        return Path(path).read_text(encoding="utf-8")

    def _load_dsl_document(self, path: PathLike) -> DSLApplication:
        """Load a DSL document from a file path."""
        from qtype.loader import load_document

        content = self._read_file_content(path)
        dsl_app, _ = load_document(content)

        if not isinstance(dsl_app, DSLApplication):
            raise ValueError(
                f"Root document is not an Application, found {type(dsl_app)}"
            )

        return dsl_app

    def _validate_dsl_document(self, document: DSLApplication) -> None:
        """Validate a DSL document, raising exceptions on errors."""
        logger.info("Validating document")

        # DSL-level validation
        from qtype.dsl.validator import validate

        validate(document)

        # Semantic-level validation (includes additional checks)
        from qtype.semantic.resolver import resolve

        resolve(document)

        logger.info("Document validation passed")

    def _resolve_semantic_model(
        self, document: DSLApplication
    ) -> SemanticApplication:
        """Resolve a DSL document to a semantic model."""
        from qtype.semantic.resolver import resolve

        return resolve(document)

    def _find_flow(
        self, semantic_model: SemanticApplication, flow_name: str | None
    ):
        """Find a flow in the semantic model by name or return the first one."""
        if flow_name:
            for flow in semantic_model.flows:
                if flow.id == flow_name:
                    return flow
            raise ValueError(f"Flow '{flow_name}' not found")

        if semantic_model.flows:
            return semantic_model.flows[0]

        raise ValueError("No flows found in application")

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
        logger.info(f"Loading and validating document: {path}")

        # Load the DSL document
        dsl_app = self._load_dsl_document(path)

        # Validate the document (raises ValidationError on failure)
        self._validate_dsl_document(dsl_app)

        logger.info("Document loaded and validated successfully")
        return dsl_app

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
        logger.info(f"Loading semantic model: {path}")

        # Load using the semantic loader directly
        from qtype.loader import load

        content = self._read_file_content(path)
        semantic_model, _ = load(content)
        return semantic_model

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
        logger.info(f"Executing workflow from {path}")

        # Load and validate document
        document = self.load_and_validate(path)

        # Execute the workflow using the document
        return self.execute_document_workflow(document, flow_name, **kwargs)

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
        # Load the DSL document
        dsl_app = self._load_dsl_document(path)

        # Validate the document (this will raise ValidationError if invalid)
        try:
            self._validate_dsl_document(dsl_app)
            return []  # No errors if we get here
        except ValidationError as e:
            return [str(e)]

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
        document = self.load_and_validate(path)

        # Generate visualization from the semantic model
        semantic_model = self._resolve_semantic_model(document)

        from qtype.semantic.visualize import visualize_application

        return visualize_application(semantic_model)

    # Convenience methods for working with loaded documents

    def execute_document_workflow(
        self,
        document: DSLApplication,
        flow_name: str | None = None,
        **kwargs: Any,
    ) -> Any:
        """Execute a workflow from an already-loaded document."""
        logger.info(f"Executing workflow: {flow_name or 'default'}")
        semantic_model = self._resolve_semantic_model(document)

        # Find the flow to execute
        target_flow = self._find_flow(semantic_model, flow_name)

        from qtype.interpreter.flow import execute_flow

        return execute_flow(target_flow, **kwargs)

    def convert_document(self, document: DocumentType) -> str:
        """Convert a document to YAML format."""

        def _wrap_if_needed(doc):
            """Wrap DSLApplication in Document if needed."""
            if isinstance(doc, DSLApplication):
                from qtype.dsl.model import Document

                return Document(root=doc)
            return doc

        # Try to use pydantic_yaml first
        try:
            from pydantic_yaml import to_yaml_str

            wrapped_doc = _wrap_if_needed(document)
            return to_yaml_str(
                wrapped_doc, exclude_unset=True, exclude_none=True
            )

        except ImportError:
            # Fallback to basic YAML if pydantic_yaml is not available
            import yaml

            wrapped_doc = _wrap_if_needed(document)
            document_dict = wrapped_doc.model_dump(
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
        import boto3  # type: ignore[import-untyped]

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

        logger.info(f"Discovered {len(model_definitions)} AWS Bedrock models")
        return model_definitions
