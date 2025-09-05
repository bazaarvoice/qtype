"""Application services for qtype operations."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from qtype.base.exceptions import LoadError, ValidationError
from qtype.base.logging import get_logger
from qtype.dsl.model import Application as DSLApplication
from qtype.semantic.model import Application as SemanticApplication

logger = get_logger("application.services")


class LoadingService:
    """Service for loading qtype documents."""

    def __init__(self) -> None:
        """Initialize the loading service."""
        self._loader = None

    def load_document(self, path: Path) -> tuple[SemanticApplication, Any]:
        """Load a qtype document from file."""
        try:
            if self._loader is None:
                from qtype.loader import load

                self._loader = load

            logger.info(f"Loading document from {path}")
            # Read the file content and pass to loader
            content = path.read_text(encoding="utf-8")
            return self._loader(content)

        except Exception as e:
            raise LoadError(f"Failed to load document from {path}: {e}") from e

    def load_document_dsl_only(self, path: Path) -> DSLApplication:
        """Load a qtype document and return only the DSL part."""
        try:
            from qtype.loader import load_document

            content = path.read_text(encoding="utf-8")
            dsl_app, _ = load_document(content)
            if not isinstance(dsl_app, DSLApplication):
                raise ValueError(
                    f"Root document is not an Application, found {type(dsl_app)}"
                )
            return dsl_app

        except Exception as e:
            raise LoadError(
                f"Failed to load DSL document from {path}: {e}"
            ) from e


class ValidationService:
    """Service for validating qtype documents."""

    def __init__(self) -> None:
        """Initialize the validation service."""
        self._validator = None
        self._resolver = None

    def validate_document(self, document: DSLApplication) -> list[str]:
        """Validate a qtype document and return any errors."""
        try:
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

        except Exception as e:
            raise ValidationError(f"Validation process failed: {e}") from e


class ConversionService:
    """Service for converting qtype documents to different formats."""

    def __init__(self) -> None:
        """Initialize the conversion service."""
        pass

    def convert_to_yaml(self, document: DSLApplication) -> str:
        """Convert document to YAML format."""
        try:
            from pydantic_yaml import to_yaml_str

            return to_yaml_str(document)
        except ImportError:
            # Fallback to standard yaml if pydantic_yaml not available
            import yaml

            return yaml.dump(document.model_dump(), default_flow_style=False)

    def convert_to_json(self, document: DSLApplication) -> str:
        """Convert document to JSON format."""
        import json

        return json.dumps(document.model_dump(), indent=2)


class GenerationService:
    """Service for generating schemas and other artifacts."""

    def __init__(self) -> None:
        """Initialize the generation service."""
        self._resolver = None

    def generate_schema(self, document: DSLApplication) -> dict[str, Any]:
        """Generate JSON schema from qtype document."""
        try:
            if self._resolver is None:
                from qtype.semantic.resolver import resolve

                self._resolver = resolve

            semantic_model = self._resolver(document)

            # For now, return the schema of the semantic model
            # TODO: Implement proper schema generation
            return semantic_model.model_json_schema()

        except Exception as e:
            raise ValidationError(f"Schema generation failed: {e}") from e


class VisualizationService:
    """Service for visualizing qtype applications."""

    def __init__(self) -> None:
        """Initialize the visualization service."""
        self._resolver = None

    def visualize_application(self, document: DSLApplication) -> str:
        """Generate visualization of the application structure."""
        try:
            if self._resolver is None:
                from qtype.semantic.resolver import resolve

                self._resolver = resolve

            semantic_model = self._resolver(document)

            from qtype.semantic.visualize import visualize_application

            return visualize_application(semantic_model)

        except Exception as e:
            raise ValidationError(
                f"Visualization generation failed: {e}"
            ) from e


class ExecutionService:
    """Service for executing qtype workflows."""

    def __init__(self) -> None:
        """Initialize the execution service."""
        self._resolver = None

    def execute_workflow(
        self,
        document: DSLApplication,
        flow_name: str | None = None,
        **kwargs: Any,
    ) -> Any:
        """Execute a qtype workflow."""
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
            from qtype.base.exceptions import InterpreterError

            raise InterpreterError(f"Workflow execution failed: {e}") from e
