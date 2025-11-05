"""
Command-line interface for validating QType YAML spec files.
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path
from typing import Any

from qtype.base.exceptions import LoadError, SemanticError, ValidationError
from qtype.dsl.linker import DuplicateComponentError, ReferenceNotFoundError
from qtype.dsl.loader import YAMLLoadError
from qtype.dsl.model import Application as DSLApplication
from qtype.dsl.model import Document
from qtype.semantic.loader import load

logger = logging.getLogger(__name__)


def main(args: Any) -> None:
    """
    Validate a QType YAML spec file against the QTypeSpec schema and semantics.

    Args:
        args: Arguments passed from the command line or calling context.

    Exits:
        Exits with code 1 if validation fails.
    """
    spec_path = Path(args.spec)

    try:
        # Load and validate the document (works for all document types)
        # This includes: YAML parsing, Pydantic validation, linking, and semantic checks
        loaded_data, custom_types = load(spec_path)
        logger.info("✅ Validation successful - document is valid.")

    except LoadError as e:
        logger.error(f"❌ Failed to load document: {e}")
        sys.exit(1)
    except YAMLLoadError as e:
        # YAML syntax errors
        logger.error(f"❌ {e}")
        sys.exit(1)
    except DuplicateComponentError as e:
        # Duplicate ID errors during linking
        logger.error(f"❌ {e}")
        sys.exit(1)
    except ReferenceNotFoundError as e:
        # Reference resolution errors during linking
        logger.error(f"❌ {e}")
        sys.exit(1)
    except ValueError as e:
        # Pydantic validation errors from parse_document
        logger.error(f"❌ {e}")
        sys.exit(1)
    except ValidationError as e:
        logger.error(f"❌ Validation failed: {e}")
        sys.exit(1)
    except SemanticError as e:
        logger.error(f"❌ Semantic validation failed: {e}")
        sys.exit(1)

    # If printing is requested, load and print the document
    if args.print:
        from pydantic_yaml import to_yaml_str

        # Wrap in Document if it's a DSL Application
        if isinstance(loaded_data, DSLApplication):
            wrapped = Document(root=loaded_data)
        else:
            wrapped = loaded_data
        logging.info(
            to_yaml_str(wrapped, exclude_unset=True, exclude_none=True)
        )


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
