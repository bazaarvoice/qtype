"""
Command-line interface for validating QType YAML spec files.
"""

import logging
import sys
from typing import Any

from pydantic import ValidationError

from qtype.dsl.validator import validate_spec
from qtype.ir.resolver import resolve_semantic_ir
from qtype.ir.validator import validate_semantics

logger = logging.getLogger(__name__)


def validate_main(args: Any) -> None:
    """
    Validate a QType YAML spec file against the QTypeSpec schema and semantics.

    Args:
        args: Arguments passed from the command line or calling context.

    Exits:
        Exits with code 1 if validation fails.
    """
    try:
        spec = validate_spec(args)
        logger.info("✅ Schema validation successful %s", spec)
    except ValidationError as exc:
        logger.error("❌ Schema validation failed:\n%s", exc)
        sys.exit(1)

    try:
        validate_semantics(spec)
        logger.info("✅ Semantic validation successful.")
    except Exception as exc:
        logger.error("❌ Semantic validation failed:\n%s", exc)
        sys.exit(1)

    try:
        resolve_semantic_ir(spec)
        logger.info("✅ Semantic resolution successful.")
    except Exception as exc:
        logger.error("❌ Semantic resolution failed:\n%s", exc)
        sys.exit(1)
