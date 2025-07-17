"""
Command-line interface for validating QType YAML spec files.
"""

import argparse
import logging
import sys
from typing import Any

from pydantic import ValidationError

from qtype import dsl
from qtype.dsl.validator import QTypeValidationError, validate
from qtype.loader import _resolve_root, load_yaml
from qtype.semantic.errors import SemanticResolutionError
from qtype.semantic.resolver import resolve

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
        yaml_data = load_yaml(args.spec)
        logging.info("✅ Schema validation successful.")
        document = dsl.Document.model_validate(yaml_data)
        logging.info("✅ Model validation successful.")
        document = _resolve_root(document)
        if not isinstance(document, dsl.Application):
            logging.warning(
                "🟨 Spec is not an Application, skipping semantic resolution."
            )
        else:
            document = validate(document)
            logger.info("✅ Language validation successful")
            document = resolve(document)
            logger.info("✅ Semantic validation successful")
        if args.print:
            logger.info(
                document.model_dump_json(  # type: ignore
                    indent=2,
                    exclude_none=True,
                )
            )

    except ValidationError as exc:
        logger.error("❌ Schema validation failed:\n%s", exc)
        sys.exit(1)
    except QTypeValidationError as exc:
        logger.error("❌ DSL validation failed:\n%s", exc)
        sys.exit(1)
    except SemanticResolutionError as exc:
        logger.error("❌ Semantic resolution failed:\n%s", exc)
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
