"""
Command-line interface for running QType YAML spec files.
"""

from __future__ import annotations

import argparse
import json
import logging
from pathlib import Path
from typing import Any

from qtype.application.facade import QTypeFacade
from qtype.base.exceptions import InterpreterError, LoadError, ValidationError

logger = logging.getLogger(__name__)


def run_flow(args: Any) -> None:
    """Run a QType YAML spec file by executing its flows.

    Args:
        args: Arguments passed from the command line or calling context.
    """
    facade = QTypeFacade()
    spec_path = Path(args.spec)

    try:
        logger.info(f"Running flow from {spec_path}")

        # Parse input JSON
        try:
            input_data = json.loads(args.input) if args.input else {}
        except json.JSONDecodeError as e:
            logger.error(f"❌ Invalid JSON input: {e}")
            return

        # Execute the workflow using the facade
        result = facade.execute_workflow(
            spec_path, flow_name=args.flow, **input_data
        )

        logger.info("✅ Flow execution completed successfully")

        # Print results
        if result:
            if hasattr(result, "__iter__") and not isinstance(result, str):
                # If result is a list of variables or similar
                try:
                    for item in result:
                        if hasattr(item, "id") and hasattr(item, "value"):
                            logger.info(f"Output {item.id}: {item.value}")
                        else:
                            logger.info(f"Result: {item}")
                except TypeError:
                    logger.info(f"Result: {result}")
            else:
                logger.info(f"Result: {result}")
        else:
            logger.info("Flow completed with no output")

    except LoadError as e:
        logger.error(f"❌ Failed to load document: {e}")
    except ValidationError as e:
        logger.error(f"❌ Validation failed: {e}")
    except InterpreterError as e:
        logger.error(f"❌ Execution failed: {e}")
    except Exception as e:
        logger.error(f"❌ Unexpected error: {e}")


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
    cmd_parser.add_argument(
        "input",
        type=str,
        nargs="?",
        default="{}",
        help="JSON blob of input values for the flow (default: {}).",
    )
    cmd_parser.add_argument(
        "spec", type=str, help="Path to the QType YAML spec file."
    )
    cmd_parser.set_defaults(func=run_flow)
