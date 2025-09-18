"""Main facade for qtype operations."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd
from pydantic import BaseModel

from qtype.base.logging import get_logger
from qtype.base.types import CustomTypeRegistry, DocumentRootType, PathLike
from qtype.dsl.base_types import StepCardinality
from qtype.dsl.model import Application as DSLApplication
from qtype.dsl.model import DocumentType
from qtype.interpreter.batch.types import BatchConfig
from qtype.semantic.model import Application as SemanticApplication
from qtype.semantic.model import Variable

logger = get_logger("application.facade")


class QTypeFacade:
    """
    Simplified interface for all qtype operations.

    This facade hides the complexity of coordinating between DSL, semantic,
    and interpreter layers, providing a clean API for common operations.
    """

    def load_dsl_document(
        self, path: PathLike
    ) -> tuple[DocumentRootType, CustomTypeRegistry]:
        from qtype.loader import load_document

        return load_document(Path(path).read_text(encoding="utf-8"))

    def telemetry(self, spec: SemanticApplication) -> None:
        if spec.telemetry:
            logger.info(
                f"Telemetry enabled with endpoint: {spec.telemetry.endpoint}"
            )
            # Register telemetry if needed
            from qtype.interpreter.telemetry import register

            register(spec.telemetry, spec.id)

    def load_semantic_model(
        self, path: PathLike
    ) -> tuple[SemanticApplication, CustomTypeRegistry]:
        """Load a document and return the resolved semantic model."""
        from qtype.loader import load

        content = Path(path).read_text(encoding="utf-8")
        return load(content)

    def execute_workflow(
        self,
        path: PathLike,
        inputs: dict | pd.DataFrame,
        flow_name: str | None = None,
        batch_config: BatchConfig | None = None,
        **kwargs: Any,
    ) -> pd.DataFrame | list[Variable]:
        """Execute a complete workflow from document to results."""
        logger.info(f"Executing workflow from {path}")

        # Load the semantic application
        semantic_model, type_registry = self.load_semantic_model(path)
        self.telemetry(semantic_model)

        # Find the flow to execute (inlined from _find_flow)
        if flow_name:
            target_flow = None
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
        if target_flow.cardinality == StepCardinality.many:
            if isinstance(inputs, dict):
                inputs = pd.DataFrame([inputs])
            if not isinstance(inputs, pd.DataFrame):
                raise ValueError(
                    "Input must be a DataFrame for flows with 'many' cardinality"
                )
            from qtype.interpreter.batch.flow import batch_execute_flow

            batch_config = batch_config or BatchConfig()
            results, errors = batch_execute_flow(
                target_flow, inputs, batch_config, **kwargs
            )  # type: ignore
            return results
        else:
            from qtype.interpreter.flow import execute_flow

            for var in target_flow.inputs:
                if var.id in inputs:
                    var.value = inputs[var.id]
            args = {**kwargs, **inputs}
            return execute_flow(target_flow, **args)

    def visualize_application(self, path: PathLike) -> str:
        """Visualize an application as Mermaid diagram."""
        from qtype.semantic.visualize import visualize_application

        semantic_model, _ = self.load_semantic_model(path)
        return visualize_application(semantic_model)

    def convert_document(self, document: DocumentType) -> str:
        """Convert a document to YAML format."""
        # Wrap DSLApplication in Document if needed
        wrapped_document: BaseModel = document
        if isinstance(document, DSLApplication):
            from qtype.dsl.model import Document

            wrapped_document = Document(root=document)
        from pydantic_yaml import to_yaml_str

        return to_yaml_str(
            wrapped_document, exclude_unset=True, exclude_none=True
        )

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
