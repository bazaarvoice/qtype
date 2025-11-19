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

import pandas as pd
from pydantic.warnings import UnsupportedFieldAttributeWarning

from qtype.application.facade import QTypeFacade
from qtype.base.exceptions import InterpreterError, LoadError, ValidationError

logger = logging.getLogger(__name__)


# Supress specific pydantic warnings that llamaindex needs to fix
warnings.filterwarnings("ignore", category=UnsupportedFieldAttributeWarning)


# supress qdrant logging
for name in ["httpx", "urllib3", "qdrant_client"]:
    logging.getLogger(name).setLevel(logging.WARNING)


def read_data_from_file(file_path: str) -> pd.DataFrame:
    """
    Reads a file into a pandas DataFrame based on its MIME type.
    """
    from pathlib import Path

    import magic

    mime_type = magic.Magic(mime=True).from_file(file_path)

    if mime_type == "text/csv":
        return pd.read_csv(file_path)
    elif mime_type == "text/plain":
        # For text/plain, use file extension to determine format
        file_ext = Path(file_path).suffix.lower()
        if file_ext == ".csv":
            return pd.read_csv(file_path)
        elif file_ext == ".json":
            return pd.read_json(file_path)
        else:
            raise ValueError(
                (
                    f"Unsupported text/plain file extension: {file_ext}. "
                    "Supported extensions: .csv, .json"
                )
            )
    elif mime_type == "application/json":
        return pd.read_json(file_path)
    elif mime_type in [
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "application/vnd.ms-excel",
    ]:
        return pd.read_excel(file_path)
    elif mime_type in ["application/vnd.parquet", "application/octet-stream"]:
        return pd.read_parquet(file_path)
    else:
        raise ValueError(
            f"Unsupported MIME type for file {file_path}: {mime_type}"
        )


def run_flow(args: Any) -> None:
    """Run a QType YAML spec file by executing its flows.

    Args:
        args: Arguments passed from the command line or calling context.
    """
    import asyncio

    facade = QTypeFacade()
    spec_path = Path(args.spec)

    try:
        logger.info(f"Running flow from {spec_path}")

        if args.input_file:
            logger.info(f"Loading input data from file: {args.input_file}")
            input: Any = read_data_from_file(args.input_file)
        else:
            # Parse input JSON
            try:
                input = json.loads(args.input) if args.input else {}
            except json.JSONDecodeError as e:
                logger.error(f"❌ Invalid JSON input: {e}")
                return

        # Execute the workflow using the facade (now async, returns DataFrame)
        result_df = asyncio.run(
            facade.execute_workflow(
                spec_path,
                flow_name=args.flow,
                inputs=input,
                show_progress=args.progress,
            )
        )

        logger.info("✅ Flow execution completed successfully")

        # Display results
        if len(result_df) > 0:
            logger.info(f"Processed {len(result_df)} em")

            # Remove 'row' and 'error' columns for display if all errors are None
            display_df = result_df.copy()
            if (
                "error" in display_df.columns
                and display_df["error"].isna().all()
            ):
                display_df = display_df.drop(columns=["error"])
            if "row" in display_df.columns:
                display_df = display_df.drop(columns=["row"])

            if len(display_df) > 1:
                logger.info(f"\nResults:\n{display_df[0:10].to_string()}\n...")
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
        "spec", type=str, help="Path to the QType YAML spec file."
    )
    cmd_parser.set_defaults(func=run_flow)
