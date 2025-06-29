"""
Command-line interface for running QType YAML spec files.
"""

from __future__ import annotations

import logging
import sys
from typing import Any

from pydantic import ValidationError

from qtype.dsl.validator import validate_spec
from qtype.ir.resolver import resolve_semantic_ir
from qtype.ir.validator import validate_semantics
from qtype.runner.executor import FlowExecutor

logger = logging.getLogger(__name__)


def run_main(args: Any) -> None:
    """
    Run a QType YAML spec file by validating, resolving, and executing it.

    Args:
        args: Arguments passed from the command line or calling context.

    Exits:
        Exits with code 1 if validation fails or no executable flows found.
    """
    # Step 1: Validate the spec
    try:
        spec = validate_spec(args)
        logger.info("✅ Schema validation successful")
    except ValidationError as exc:
        logger.error("❌ Schema validation failed:\n%s", exc)
        sys.exit(1)

    # Step 2: Validate semantics
    try:
        validate_semantics(spec)
        logger.info("✅ Semantic validation successful.")
    except Exception as exc:
        logger.error("❌ Semantic validation failed:\n%s", exc)
        sys.exit(1)

    # Step 3: Resolve semantic IR
    try:
        ir_spec = resolve_semantic_ir(spec)
        logger.info("✅ Semantic resolution successful.")
    except Exception as exc:
        logger.error("❌ Semantic resolution failed:\n%s", exc)
        sys.exit(1)

    # Step 4: Find and execute flows
    if not ir_spec.flows:
        logger.error("❌ No flows found in specification.")
        sys.exit(1)

    # For now, only support 'complete' mode flows
    complete_flows = [
        flow for flow in ir_spec.flows if flow.mode.value == "complete"
    ]

    if not complete_flows:
        logger.error("❌ No 'complete' mode flows found. Only 'complete' mode is currently supported.")
        sys.exit(1)

    # Use the first complete flow
    flow = complete_flows[0]
    if len(complete_flows) > 1:
        logger.warning(
            f"⚠️  Multiple complete flows found. Using flow '{flow.id}'."
        )

    logger.info(f"🚀 Running flow '{flow.id}'...")

    # Step 5: Execute the flow
    try:
        executor = FlowExecutor(ir_spec)
        result = executor.execute_flow(flow)

        logger.info("✅ Flow execution completed successfully.")
        if result:
            print("\n" + "=" * 50)
            print("RESULT:")
            print("=" * 50)
            print(result)
            print("=" * 50)

    except Exception as exc:
        logger.error("❌ Flow execution failed:\n%s", exc)
        sys.exit(1)
