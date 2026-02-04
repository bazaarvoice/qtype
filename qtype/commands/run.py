"""
Command-line interface for running QType YAML spec files.
"""

from __future__ import annotations

import argparse
import json
import logging
import warnings
from pathlib import Path
from typing import Any

from pydantic.warnings import UnsupportedFieldAttributeWarning

from qtype.base.exceptions import InterpreterError, LoadError, ValidationError
from qtype.interpreter.converters import read_dataframe_from_file

logger = logging.getLogger(__name__)


# Supress specific pydantic warnings that llamaindex needs to fix
warnings.filterwarnings("ignore", category=UnsupportedFieldAttributeWarning)


# supress qdrant logging
for name in ["httpx", "urllib3", "qdrant_client", "opensearch"]:
    logging.getLogger(name).setLevel(logging.WARNING)


def register_telemetry(spec) -> None:
    """Register telemetry if enabled in the spec."""
    from qtype.interpreter.telemetry import register
    from qtype.semantic.model import Application as SemanticApplication

    if isinstance(spec, SemanticApplication) and spec.telemetry:
        logger.info(
            f"Telemetry enabled with endpoint: {spec.telemetry.endpoint}"
        )
        secret_mgr = create_secret_manager_for_spec(spec)
        register(spec.telemetry, secret_mgr, spec.id)


def create_secret_manager_for_spec(spec):
    """Create a secret manager based on the specification."""
    from qtype.interpreter.base.secrets import create_secret_manager
    from qtype.semantic.model import Application as SemanticApplication

    if isinstance(spec, SemanticApplication):
        return create_secret_manager(spec.secret_manager)
    else:
        raise ValueError(
            "Can't create secret manager for non-Application spec"
        )


async def execute_workflow(
    path: Path,
    inputs: dict | Any,
    flow_name: str | None = None,
    **kwargs: Any,
) -> Any:
    """Execute a complete workflow from document to results.

    Args:
        path: Path to the QType specification file
        inputs: Dictionary of input values or DataFrame for batch
        flow_name: Optional name of flow to execute
        **kwargs: Additional dependencies for execution

    Returns:
        DataFrame with results (one row per input)
    """
    import pandas as pd
    from opentelemetry import trace

    from qtype.interpreter.base.executor_context import ExecutorContext
    from qtype.interpreter.converters import (
        dataframe_to_flow_messages,
        flow_messages_to_dataframe,
    )
    from qtype.interpreter.flow import run_flow
    from qtype.interpreter.types import Session
    from qtype.semantic.loader import load
    from qtype.semantic.model import Application as SemanticApplication

    # Load the semantic application
    semantic_model, type_registry = load(path)
    assert isinstance(semantic_model, SemanticApplication)
    register_telemetry(semantic_model)

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

    logger.info(f"Executing flow {target_flow.id} from {path}")

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
    session = Session(
        session_id=kwargs.pop("session_id", "default"),
        conversation_history=kwargs.pop("conversation_history", []),
    )

    # Convert DataFrame to FlowMessages with type conversion
    initial_messages_list = dataframe_to_flow_messages(
        input_df, target_flow.inputs, session=session
    )

    # Execute the flow
    secret_manager = create_secret_manager_for_spec(semantic_model)

    context = ExecutorContext(
        secret_manager=secret_manager,
        tracer=trace.get_tracer(__name__),
    )
    results = await run_flow(
        target_flow,
        initial_messages_list,
        context=context,
        **kwargs,
    )

    # Convert results back to DataFrame
    results_df = flow_messages_to_dataframe(results, target_flow)

    return results_df


def run_flow(args: Any) -> None:
    """Run a QType YAML spec file by executing its flows.

    Args:
        args: Arguments passed from the command line or calling context.
    """
    import asyncio

    spec_path = Path(args.spec)

    try:
        logger.info(f"Running flow from {spec_path}")

        if args.input_file:
            logger.info(f"Loading input data from file: {args.input_file}")
            input: Any = read_dataframe_from_file(args.input_file)
        else:
            # Parse input JSON
            try:
                input = json.loads(args.input) if args.input else {}
            except json.JSONDecodeError as e:
                logger.error(f"❌ Invalid JSON input: {e}")
                return

        # Execute the workflow using the standalone function
        result_df = asyncio.run(
            execute_workflow(
                spec_path,
                flow_name=args.flow,
                inputs=input,
                show_progress=args.progress,
            )
        )

        logger.info("✅ Flow execution completed successfully")

        # Display results
        if len(result_df) > 0:
            logger.info(f"Processed {len(result_df)} rows")

            # Remove 'row' and 'error' columns for display if all errors are None
            display_df = result_df.copy()
            if (
                "error" in display_df.columns
                and display_df["error"].isna().all()
            ):
                display_df = display_df.drop(columns=["error"])
            if "row" in display_df.columns:
                display_df = display_df.drop(columns=["row"])

            # Show summary for console display
            logger.info(
                f"\nResults summary: {len(display_df)} rows, "
                f"{len(display_df.columns)} columns: {list(display_df.columns)}"
            )

            # Optionally show full output
            if args.show_output:
                # Truncate long strings for display
                max_col_width = 100
                for col in display_df.columns:
                    display_df[col] = display_df[col].apply(
                        lambda x: (
                            f"{str(x)[:max_col_width]}..."
                            if isinstance(x, str)
                            and len(str(x)) > max_col_width
                            else x
                        )
                    )

                if len(display_df) > 1:
                    logger.info(
                        f"\nResults:\n{display_df[0:10].to_string()}\n..."
                    )
                else:
                    # Print the first row with column_name: value one per line
                    fmt_str = []
                    for col, val in display_df.iloc[0].items():
                        fmt_str.append(f"{col}: {val}")
                    fmt_str = "\n".join(fmt_str)
                    logger.info(f"\nResults:\n{fmt_str}")

            # Save the output
            if args.output:
                # Save full DataFrame with row and error columns
                result_df.to_parquet(args.output)
                logger.info(f"Output saved to {args.output}")
        else:
            logger.info("Flow completed with no output")

    except LoadError as e:
        logger.error(f"❌ Failed to load document: {e}")
    except ValidationError as e:
        logger.error(f"❌ Validation failed: {e}")
    except InterpreterError as e:
        logger.error(f"❌ Execution failed: {e}")


def parser(subparsers: argparse._SubParsersAction) -> None:
    """Set up the run subcommand parser.

    Args:
        subparsers: The subparsers object to add the command to.
    """
    cmd_parser = subparsers.add_parser(
        "run", help="Executes a QType Application locally"
    )
    cmd_parser.add_argument(
        "-f",
        "--flow",
        type=str,
        default=None,
        help="The name of the flow to run. If not specified, runs the first flow found.",
    )
    # Allow either a direct JSON string or an input file
    input_group = cmd_parser.add_mutually_exclusive_group()
    input_group.add_argument(
        "-i",
        "--input",
        type=str,
        default="{}",
        help="JSON blob of input values for the flow (default: {}).",
    )
    input_group.add_argument(
        "-I",
        "--input-file",
        type=str,
        default=None,
        help="Path to a file (e.g., CSV, JSON, Parquet) with input data for batch processing.",
    )
    cmd_parser.add_argument(
        "-o",
        "--output",
        type=str,
        default=None,
        help="Path to save output data. If input is a DataFrame, output will be saved as parquet. If single result, saved as JSON.",
    )
    cmd_parser.add_argument(
        "--progress",
        action="store_true",
        help="Show progress bars during flow execution.",
    )
    cmd_parser.add_argument(
        "--show-output",
        action="store_true",
        help="Display full output data in console (default: summary only).",
    )

    cmd_parser.add_argument(
        "spec", type=str, help="Path to the QType YAML spec file."
    )
    cmd_parser.set_defaults(func=run_flow)
