"""
Command-line interface for validating QType YAML spec files.
"""

import argparse
import logging
import sys
from typing import Any

from pydantic import BaseModel, ValidationError

from qtype import dsl
from qtype.dsl.loader import load
from qtype.semantic.resolver import SemanticResolutionError, resolve

logger = logging.getLogger(__name__)


def main(args: Any) -> None:
    """
    Validate a QType YAML spec file against the QTypeSpec schema and semantics.

    Args:
        args: Arguments passed from the command line or calling context.

    Exits:
        Exits with code 1 if validation fails.
    """
    try:
        spec = load(args.spec)
        if isinstance(spec, dsl.Application):
            spec = resolve(spec)
        else:
            logger.info(f"Spec is a {spec.__class__.__name__}, skipping semantic resolution.")
        logger.info("✅ Schema validation successful")
        if args.print:

            def print_model(s: BaseModel) -> None:
                logger.info(s.model_dump_json(indent=2))

            if isinstance(spec, list):
                for s in spec:
                    print_model(s)
            else:
                print_model(spec)
    except ValidationError as exc:
        logger.error("❌ Schema validation failed:\n%s", exc)
        sys.exit(1)
    except SemanticResolutionError as exc:
        logger.error("❌ Semantic resolution failed:\n%s", exc)
        sys.exit(1)

    # try:
    #     validate_semantics(spec)
    #     logger.info("✅ Semantic validation successful.")
    # except Exception as exc:
    #     logger.error("❌ Semantic validation failed:\n%s", exc)
    #     sys.exit(1)

    # try:
    #     _ir = resolve_semantic_ir(spec)
    #     logger.info("✅ Semantic resolution successful.")
    # except Exception as exc:
    #     logger.error("❌ Semantic resolution failed:\n%s", exc, exc_info=True)
    #     sys.exit(1)


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
