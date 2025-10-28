"""Main facade for qtype operations."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd
from pydantic import BaseModel

from qtype.base.logging import get_logger
from qtype.base.types import CustomTypeRegistry, PathLike
from qtype.dsl.model import Application as DSLApplication
from qtype.dsl.model import DocumentType
from qtype.semantic.model import Application as SemanticApplication
from qtype.semantic.model import DocumentType as SemanticDocumentType

logger = get_logger("application.facade")


class QTypeFacade:
    """
    Simplified interface for all qtype operations.

    This facade hides the complexity of coordinating between DSL, semantic,
    and interpreter layers, providing a clean API for common operations.
    """

    def load_dsl_document(
        self, path: PathLike
    ) -> tuple[DocumentType, CustomTypeRegistry]:
        from qtype.dsl.loader import load_yaml_file
        from qtype.dsl.parser import parse_document

        yaml_data = load_yaml_file(Path(path))
        return parse_document(yaml_data)

    def telemetry(self, spec: SemanticDocumentType) -> None:
        if isinstance(spec, SemanticApplication) and spec.telemetry:
            logger.info(
                f"Telemetry enabled with endpoint: {spec.telemetry.endpoint}"
            )
            # Register telemetry if needed
            from qtype.interpreter.telemetry import register

            register(spec.telemetry, spec.id)

    def load_semantic_model(
        self, path: PathLike
    ) -> tuple[SemanticDocumentType, CustomTypeRegistry]:
        """Load a document and return the resolved semantic model."""
        from qtype.semantic.loader import load

        return load(Path(path))

    async def execute_workflow(
        self,
        path: PathLike,
        inputs: dict | pd.DataFrame,
        flow_name: str | None = None,
        **kwargs: Any,
    ) -> pd.DataFrame:
        """
        Execute a complete workflow from document to results.

        Args:
            path: Path to the QType specification file
            inputs: Dictionary of input values or DataFrame for batch
            flow_name: Optional name of flow to execute
            **kwargs: Additional dependencies for execution

        Returns:
            DataFrame with results (one row per input)
        """
        logger.info(f"Executing workflow from {path}")

        # Load the semantic application
        semantic_model, type_registry = self.load_semantic_model(path)
        assert isinstance(semantic_model, SemanticApplication)
        self.telemetry(semantic_model)

        # Find the flow to execute
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

        # Convert inputs to DataFrame (normalize single dict to 1-row DataFrame)
        if isinstance(inputs, dict):
            input_df = pd.DataFrame([inputs])
        elif isinstance(inputs, pd.DataFrame):
            input_df = inputs
        else:
            raise ValueError(
                f"Inputs must be dict or DataFrame, got {type(inputs)}"
            )

        # Create session
        from qtype.interpreter.converters import (
            dataframe_to_flow_messages,
            flow_messages_to_dataframe,
        )
        from qtype.interpreter.types import Session

        session = Session(
            session_id=kwargs.pop("session_id", "default"),
            conversation_history=kwargs.pop("conversation_history", []),
        )

        # Convert DataFrame to FlowMessages
        initial_messages = dataframe_to_flow_messages(input_df, session)

        # Execute the flow
        from qtype.interpreter.flow import run_flow

        results = await run_flow(target_flow, initial_messages, **kwargs)

        # Convert results back to DataFrame
        results_df = flow_messages_to_dataframe(results, target_flow)

        return results_df

    def visualize_application(self, path: PathLike) -> str:
        """Visualize an application as Mermaid diagram."""
        from qtype.semantic.visualize import visualize_application

        semantic_model, _ = self.load_semantic_model(path)
        assert isinstance(semantic_model, SemanticApplication)
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
