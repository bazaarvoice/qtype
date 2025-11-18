"""Main facade for qtype operations."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from qtype.base.types import PathLike
from qtype.semantic.model import Application as SemanticApplication
from qtype.semantic.model import DocumentType as SemanticDocumentType

# Note: There should be _zero_ imports here at the top that import qtype.interpreter.
# That's the whole point of this facade - to avoid importing optional
# dependencies unless these methods are called.

logger = logging.getLogger(__name__)


class QTypeFacade:
    """
    Simplified interface for qtype operations.

    This facade provides lazy-loading wrappers for operations that require
    optional dependencies (interpreter package), allowing base qtype to work
    without those dependencies installed.
    """

    def telemetry(self, spec: SemanticDocumentType) -> None:
        if isinstance(spec, SemanticApplication) and spec.telemetry:
            logger.info(
                f"Telemetry enabled with endpoint: {spec.telemetry.endpoint}"
            )
            # Register telemetry if needed
            from qtype.interpreter.telemetry import register

            register(spec.telemetry, self.secret_manager(spec), spec.id)

    def secret_manager(self, spec: SemanticDocumentType):
        """
        Create a secret manager based on the specification.

        Args:
            spec: SemanticDocumentType specification

        Returns:
            Secret manager instance
        """
        from qtype.interpreter.base.secrets import create_secret_manager

        if isinstance(spec, SemanticApplication):
            return create_secret_manager(spec.secret_manager)
        else:
            raise ValueError(
                "Can't create secret manager for non-Application spec"
            )

    async def execute_workflow(
        self,
        path: PathLike,
        inputs: dict | Any,
        flow_name: str | None = None,
        **kwargs: Any,
    ) -> Any:
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
        import pandas as pd

        from qtype.semantic.loader import load

        logger.info(f"Executing workflow from {path}")

        # Load the semantic application
        semantic_model, type_registry = load(Path(path))
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
        from opentelemetry import trace

        from qtype.interpreter.base.executor_context import ExecutorContext
        from qtype.interpreter.flow import run_flow

        secret_manager = self.secret_manager(semantic_model)
        context = ExecutorContext(
            secret_manager=secret_manager,
            tracer=trace.get_tracer(__name__),
        )
        results = await run_flow(
            target_flow,
            initial_messages,
            context=context,
            **kwargs,
        )

        # Convert results back to DataFrame
        results_df = flow_messages_to_dataframe(results, target_flow)

        return results_df

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
