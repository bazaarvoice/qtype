"""
Command-line interface for running QType YAML spec files.
"""

from __future__ import annotations

import argparse
import json
import logging
from pathlib import Path
from typing import Any

import magic
import pandas as pd

from qtype.application.facade import QTypeFacade
from qtype.base.exceptions import InterpreterError, LoadError, ValidationError

logger = logging.getLogger(__name__)


def read_data_from_file(file_path: str) -> pd.DataFrame:
    """
    Reads a file into a pandas DataFrame based on its MIME type.
    """
    mime_type = magic.Magic(mime=True).from_file(file_path)

    if mime_type == "text/csv":
        return pd.read_csv(file_path)
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
    facade = QTypeFacade()
    spec_path = Path(args.spec)

    try:
        logger.info(f"Running flow from {spec_path}")

        if args.input_file:
            logger.info(f"Loading input data from file: {args.input_file}")
            input = read_data_from_file(args.input_file)
        else:
            # Parse input JSON
            try:
                input = json.loads(args.input) if args.input else {}
            except json.JSONDecodeError as e:
                logger.error(f"❌ Invalid JSON input: {e}")
                return

        # Execute the workflow using the facade
        result = facade.execute_workflow(
            spec_path, flow_name=args.flow, inputs=input, batch_config=None
        )

        logger.info("✅ Flow execution completed successfully")

        # Print results
        if isinstance(result, pd.DataFrame):
            logging.info("Output DataFrame:")
            logging.info(result)
        elif (
            result
            and hasattr(result, "__iter__")
            and not isinstance(result, str)
        ):
            # If result is a list of variables or similar
            try:
                for item in result:
                    if hasattr(item, "id") and hasattr(item, "value"):
                        logger.info(f"Output {item.id}: {item.value}")
                    else:
                        logger.info(f"Result: {item}")
            except TypeError:
                logger.info(f"Result: {result}")
        elif isinstance(result, str):
            logger.info(f"Result: {result}")
        else:
            logger.info("Flow completed with no output")

        # save the output
        if isinstance(result, pd.DataFrame) and args.output:
            result.to_parquet(args.output)
            logger.info(f"Output DataFrame saved to {args.output}")
        elif args.output:
            with open(args.output, "w") as f:
                json.dump(result, f, indent=2)
            logger.info(f"Output saved to {args.output}")

    except LoadError as e:
        logger.error(f"❌ Failed to load document: {e}")
    except ValidationError as e:
        logger.error(f"❌ Validation failed: {e}")
    except InterpreterError as e:
        logger.error(f"❌ Execution failed: {e}")
    except Exception as e:
        logger.error(f"❌ Unexpected error: {e}", exc_info=True)


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
        "spec", type=str, help="Path to the QType YAML spec file."
    )
    cmd_parser.set_defaults(func=run_flow)
