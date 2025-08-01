"""
Command-line interface for running QType YAML spec files.
"""

from __future__ import annotations

import argparse
import logging
from typing import Any

from qtype.dsl.domain_types import ChatMessage
from qtype.interpreter.flow import execute_flow
from qtype.interpreter.typing import create_input_type_model
from qtype.loader import load
from qtype.semantic.model import Application, Flow, Step

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

    return flow


def _telemetry(spec: Application) -> None:
    if spec.telemetry:
        logger.info(
            f"Telemetry enabled with endpoint: {spec.telemetry.endpoint}"
        )
        # Register telemetry if needed
        from qtype.interpreter.telemetry import register

        register(spec.telemetry, spec.id)


def run_flow(args: Any) -> None:
    """Run a QType YAML spec file by executing its flows.

    Args:
        args: Arguments passed from the command line or calling context.
    """
    spec = load(args.spec)

    flow = _get_flow(spec, args.flow)
    logger.info(f"Executing flow: {flow.id}")
    input_type = create_input_type_model(flow)
    inputs = input_type.model_validate_json(args.input)
    for var in flow.inputs:
        # Get the value from the request using the variable ID
        inputs_dict = inputs.model_dump()  # type: ignore
        if var.id in inputs_dict:
            var.value = getattr(inputs, var.id)
    _telemetry(spec)

    was_streamed = False
    previous: str = ""

    def stream_fn(step: Step, msg: ChatMessage | str) -> None:
        """Stream function to handle step outputs."""
        nonlocal was_streamed, previous
        if step == flow.steps[-1]:
            was_streamed = True
            if isinstance(msg, ChatMessage):
                content = " ".join(
                    [m.content for m in msg.blocks if m.content]
                )
                # Note: streaming chat messages accumulate the content...
                content = content.removeprefix(previous)
                print(content, end="", flush=True)
                previous += content
            else:
                print(msg, end="", flush=True)

    result = execute_flow(flow, stream_fn=stream_fn)  # type: ignore
    if not was_streamed:
        logger.info(
            f"Flow execution result: {', '.join([f'{var.id}: {var.value}' for var in result])}"
        )
    else:
        print("\n")


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
        help="JSON blob of input values for the flow.",
    )

    cmd_parser.add_argument(
        "spec", type=str, help="Path to the QType YAML spec file."
    )

    cmd_parser.set_defaults(func=run_flow)
