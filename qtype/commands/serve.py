"""
Command-line interface for serving QType YAML spec files as web APIs.
"""

from __future__ import annotations

import argparse
import logging
import os
from pathlib import Path
from typing import Any

import uvicorn

from qtype.base.exceptions import ValidationError
from qtype.semantic.loader import load
from qtype.semantic.model import Application

logger = logging.getLogger(__name__)


def create_api_app() -> Any:
    """Factory function to create FastAPI app.

    Returns:
        FastAPI application instance.

    Raises:
        RuntimeError: If QTYPE_SPEC_PATH not set in environment.
        ValidationError: If spec is not an Application document.
    """
    from qtype.interpreter.api import APIExecutor

    spec_path_str = os.environ["_QTYPE_SPEC_PATH"]

    spec_path = Path(spec_path_str)
    logger.info(f"Loading spec: {spec_path}")

    semantic_model, _ = load(spec_path)
    if not isinstance(semantic_model, Application):
        raise ValidationError("Can only serve Application documents")

    logger.info(f"✅ Successfully loaded spec: {spec_path}")

    # Derive name from spec filename
    name = spec_path.name.replace(".qtype.yaml", "").replace("_", " ").title()

    # Get host/port from environment (set by uvicorn)
    host = os.environ["_QTYPE_HOST"]
    port = int(os.environ["_QTYPE_PORT"])

    # Create server info for OpenAPI spec
    servers = [
        {
            "url": f"http://{host}:{port}",
            "description": "Development server",
        }
    ]

    api_executor = APIExecutor(semantic_model, host, port)
    return api_executor.create_app(
        name=name,
        ui_enabled=True,
        servers=servers,
    )


def serve(args: argparse.Namespace) -> None:
    """Run a QType YAML spec file as an API.

    Args:
        args: Arguments passed from the command line.
    """
    # Set environment variables for factory function
    os.environ["_QTYPE_SPEC_PATH"] = args.spec
    os.environ["_QTYPE_HOST"] = args.host
    os.environ["_QTYPE_PORT"] = str(args.port)

    logger.info(
        f"Starting server on {args.host}:{args.port}"
        f"{' (reload enabled)' if args.reload else ''}"
    )

    # Use factory mode with import string
    uvicorn.run(
        "qtype.commands.serve:create_api_app",
        factory=True,
        host=args.host,
        port=args.port,
        log_level="info",
        reload=args.reload,
        reload_includes=[args.spec] if args.reload else None,
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
        "--reload",
        action="store_true",
        help="Enable auto-reload on code changes (default: False).",
    )
    cmd_parser.set_defaults(func=serve)

    cmd_parser.add_argument(
        "spec", type=str, help="Path to the QType YAML spec file."
    )
