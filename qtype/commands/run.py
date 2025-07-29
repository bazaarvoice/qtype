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


def run_api(args: Any) -> None:
    """Run a QType YAML spec file as an API.

    Args:
        args: Arguments passed from the command line or calling context.
    """
    spec = load(args.spec)
    logger.info(f"Running API for spec: {args.spec}")
    from qtype.interpreter.api import APIExecutor

    # Get the name from the spec filename.
    # so if filename is tests/specs/full_application_test.qtype.yaml, name should be "Full Application Test"
    name = (
        args.spec.split("/")[-1]
        .replace(".qtype.yaml", "")
        .replace("_", " ")
        .title()
    )

    _telemetry(spec)
    api_executor = APIExecutor(spec)
    fastapi_app = api_executor.create_app(name=name)

    import uvicorn

    uvicorn.run(
        fastapi_app,
        host=args.host,
        port=args.port,
        log_level="info",
    )


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
