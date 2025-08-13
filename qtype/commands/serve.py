"""
Command-line interface for running QType YAML spec files.
"""

from __future__ import annotations

import argparse
import logging
from typing import Any

import uvicorn

from qtype.commands.run import _telemetry
from qtype.loader import load

logger = logging.getLogger(__name__)


def serve(args: Any) -> None:
    """Run a QType YAML spec file as an API.

    Args:
        args: Arguments passed from the command line or calling context.
    """
    spec, _ = load(args.spec)
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
    fastapi_app = api_executor.create_app(
        name=name, ui_enabled=not args.disable_ui
    )

    uvicorn.run(
        fastapi_app,
        host=args.host,
        port=args.port,
        log_level="info",
    )


def parser(subparsers: argparse._SubParsersAction) -> None:
    """Set up the run subcommand parser.

    Args:
        subparsers: The subparsers object to add the command to.
    """
    cmd_parser = subparsers.add_parser(
        "serve", help="Serve a web experience for a QType application"
    )

    cmd_parser.add_argument("-p", "--port", type=int, default=8000)
    cmd_parser.add_argument("-H", "--host", type=str, default="localhost")
    cmd_parser.add_argument(
        "--disable-ui",
        action="store_true",
        help="Disable the UI for the QType application.",
    )
    cmd_parser.set_defaults(func=serve)

    cmd_parser.add_argument(
        "spec", type=str, help="Path to the QType YAML spec file."
    )
