"""
Command-line interface for serving QType YAML spec files as web APIs.
"""

from __future__ import annotations

import argparse
import logging
from pathlib import Path
from typing import Any

import uvicorn

from qtype.application.facade import QTypeFacade
from qtype.base.exceptions import LoadError, ValidationError
from qtype.semantic.loader import load
from qtype.semantic.model import Application

logger = logging.getLogger(__name__)


def serve(args: Any) -> None:
    """Run a QType YAML spec file as an API.

    Args:
        args: Arguments passed from the command line or calling context.
    """
    facade = QTypeFacade()

    try:
        # Load and validate the document
        spec_path = Path(args.spec)
        logger.info(f"Loading and validating spec: {spec_path}")

        semantic_model, type_registry = load(spec_path)
        assert isinstance(semantic_model, Application), (
            "Can only serve Application documents"
        )
        facade.telemetry(semantic_model)
        logger.info(f"✅ Successfully loaded spec: {spec_path}")

        # Import APIExecutor and create the FastAPI app
        from qtype.interpreter.api import APIExecutor

        # Get the name from the spec filename
        name = (
            spec_path.name.replace(".qtype.yaml", "").replace("_", " ").title()
        )

        logger.info(f"Starting server for: {name}")
        api_executor = APIExecutor(semantic_model)

        # Create server info for OpenAPI spec
        servers = [
            {
                "url": f"http://{args.host}:{args.port}",
                "description": "Development server",
            }
        ]

        fastapi_app = api_executor.create_app(
            name=name, ui_enabled=not args.disable_ui, servers=servers
        )

        # Start the server
        uvicorn.run(
            fastapi_app, host=args.host, port=args.port, log_level="info"
        )

    except LoadError as e:
        logger.error(f"❌ Failed to load document: {e}")
        exit(1)
    except ValidationError as e:
        logger.error(f"❌ Validation failed: {e}")
        exit(1)
    # except Exception as e:
    #     logger.error(f"❌ Unexpected error starting server: {e}")
    #     exit(1)


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
