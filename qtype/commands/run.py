"""
Command-line interface for running QType YAML spec files.
"""

from __future__ import annotations

import argparse
import json
import logging
from typing import Any

from qtype.interpreter.flow import execute_flow
from qtype.loader import load
from qtype.semantic.model import Application, Flow

# from qtype.ir.resolver import resolve_semantic_ir
# from qtype.ir.validator import validate_semantics
# from qtype.runner.executor import FlowExecutor

logger = logging.getLogger(__name__)


def _get_flow(app: Application, flow_id: str | None) -> Flow:
    if len(app.flows) == 0:
        raise ValueError(
            "No flows found in the application."
            " Please ensure the spec contains at least one flow."
        )

    if flow_id is not None:
        # find the first flow in the list with the given flow_id
        flow = next((f for f in app.flows if f.id == flow_id), None)
        if flow is None:
            raise ValueError(f"Flow not found: {flow_id}")

    else:
        flow = app.flows[0]
        logger.warning(
            f"No flow_id specified, running flow {flow.id} by default."
        )

    return flow


def run_api(args: Any) -> None:
    pass


def run_flow(args: Any) -> None:
    """Run a QType YAML spec file by executing its flows.

    Args:
        args: Arguments passed from the command line or calling context.
    """
    spec = load(args.spec)
    logger.info(f"Running flow from spec: {spec}")

    flow = _get_flow(spec, args.flow)
    logger.info(f"Executing flow: {flow.id}")
    inputs = json.loads(args.input)
    for var in flow.inputs:
        if var.id in inputs:
            var.value = inputs[var.id]
        else:
            raise ValueError(
                f"Input variable {var.id} not found in provided input JSON."
            )
    if spec.telemetry:
        logger.info(
            f"Telemetry enabled with endpoint: {spec.telemetry.endpoint}"
        )
        # Register telemetry if needed
        from qtype.interpreter.telemetry import register

        register(spec.telemetry, spec.id)
    result = execute_flow(flow)
    logger.info(
        f"Flow execution result: {', '.join([f'{var.id}: {var.value}' for var in result])}"
    )


def run_ui(args: Any) -> None:
    """Run a QType YAML spec file by executing its flows in a UI.

    Args:
        args: Arguments passed from the command line or calling context.
    """
    # Placeholder for actual implementation
    logger.info(f"Running UI for spec: {args.spec}")
    # Here you would implement the logic to run the flow in a UI context


def parser(subparsers: argparse._SubParsersAction) -> None:
    """Set up the run subcommand parser.

    Args:
        subparsers: The subparsers object to add the command to.
    """
    cmd_parser = subparsers.add_parser(
        "run", help="Run a QType YAML spec by executing its flows."
    )

    run_subparsers = cmd_parser.add_subparsers(
        dest="run_method", required=True
    )

    # Parse for generating API runner
    api_runner_parser = run_subparsers.add_parser(
        "api", help="Serves the qtype file as an API."
    )
    api_runner_parser.add_argument(
        "-H", "--host", type=str, default="localhost"
    )
    api_runner_parser.add_argument("-p", "--port", type=int, default=8000)
    api_runner_parser.set_defaults(func=run_api)

    # Parse for running a flow
    flow_parser = run_subparsers.add_parser(
        "flow", help="Runs a QType YAML spec file by executing its flows."
    )
    flow_parser.add_argument(
        "-f",
        "--flow",
        type=str,
        default=None,
        help="The name of the flow to run. If not specified, runs the first flow found.",
    )
    flow_parser.add_argument(
        "input",
        type=str,
        help="JSON blob of input values for the flow.",
    )

    flow_parser.set_defaults(func=run_flow)

    # Run a user interface for the spec
    ui_parser = run_subparsers.add_parser(
        "ui",
        help="Runs a QType YAML spec file by executing its flows in a UI.",
    )
    ui_parser.add_argument(
        "-f",
        "--flow",
        type=str,
        default=None,
        help="The name of the flow to run in the UI. If not specified, runs the first flow found.",
    )
    ui_parser.set_defaults(func=run_ui)
    cmd_parser.add_argument(
        "spec", type=str, help="Path to the QType YAML spec file."
    )
