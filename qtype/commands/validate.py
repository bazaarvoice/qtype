"""
Command-line interface for validating QType YAML spec files.
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path
from typing import Any

from qtype import dsl
from qtype.application.facade import QTypeFacade
from qtype.base.exceptions import LoadError, SemanticError, ValidationError

logger = logging.getLogger(__name__)


def main(args: Any) -> None:
    """
    Validate a QType YAML spec file against the QTypeSpec schema and semantics.

    Args:
        args: Arguments passed from the command line or calling context.

    Exits:
        Exits with code 1 if validation fails.
    """
    facade = QTypeFacade()
    spec_path = Path(args.spec)

    try:
        # Use the facade for validation - it will raise exceptions on errors
        loaded_data, custom_types = facade.load_dsl_document(spec_path)
        if isinstance(loaded_data, dsl.Application):
            loaded_data, custom_types = facade.load_semantic_model(spec_path)
        logger.info("✅ Validation successful - document is valid.")

        # If printing is requested, load and print the document
        if args.print:
            try:
                print(loaded_data.model_dump_json(indent=2, exclude_none=True))  # type: ignore
            except Exception as e:
                logger.warning(f"Could not print document: {e}")

    except LoadError as e:
        logger.error(f"❌ Failed to load document: {e}")
        sys.exit(1)
    except ValidationError as e:
        logger.error(f"❌ Validation failed: {e}")
        sys.exit(1)
    except SemanticError as e:
        logger.error(f"❌ Semantic validation failed: {e}")
        sys.exit(1)


def parser(subparsers: argparse._SubParsersAction) -> None:
    """Set up the validate subcommand parser.

    Args:
        subparsers: The subparsers object to add the command to.
    """
    cmd_parser = subparsers.add_parser(
        "validate", help="Validate a QType YAML spec against the schema."
    )
    cmd_parser.add_argument(
        "spec", type=str, help="Path to the QType YAML spec file."
    )
    cmd_parser.add_argument(
        "-p",
        "--print",
        action="store_true",
        help="Print the spec after validation (default: False)",
    )
    cmd_parser.set_defaults(func=main)
