"""
Command-line interface for serving QType YAML spec files as web APIs.
"""

from __future__ import annotations

import argparse
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import uvicorn

from qtype.base.exceptions import ValidationError
from qtype.semantic.loader import load
from qtype.semantic.model import Application

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ServerConfig:
    """Configuration for API server."""

    spec_path: Path
    name: str
    ui_enabled: bool
    host: str
    port: int

    @property
    def servers(self) -> list[dict[str, str]]:
        """Generate server list for OpenAPI spec."""
        return [
            {
                "url": f"http://{self.host}:{self.port}",
                "description": "Development server",
            }
        ]

    @classmethod
    def from_args(cls, args: argparse.Namespace) -> ServerConfig:
        """Create configuration from CLI arguments."""
        spec_path = Path(args.spec)
        name = (
            spec_path.name.replace(".qtype.yaml", "").replace("_", " ").title()
        )
        return cls(
            spec_path=spec_path,
            name=name,
            ui_enabled=not args.disable_ui,
            host=args.host,
            port=args.port,
        )


# Module-level config for uvicorn reload factory
_reload_config: ServerConfig | None = None


def create_api_app() -> Any:
    """Factory function to create FastAPI app.

    Returns:
        FastAPI application instance.

    Raises:
        RuntimeError: If called without config being set.
        ValidationError: If spec is not an Application document.
    """
    if _reload_config is None:
        raise RuntimeError("Reload config not initialized")

    from qtype.interpreter.api import APIExecutor

    config = _reload_config
    logger.info(f"Loading spec: {config.spec_path}")

    semantic_model, _ = load(config.spec_path)
    if not isinstance(semantic_model, Application):
        raise ValidationError("Can only serve Application documents")

    logger.info(f"✅ Successfully loaded spec: {config.spec_path}")

    api_executor = APIExecutor(semantic_model, config.host, config.port)
    return api_executor.create_app(
        name=config.name,
        ui_enabled=config.ui_enabled,
        servers=config.servers,
    )


def _run_server(config: ServerConfig, reload: bool) -> None:
    """Start the uvicorn server.

    Args:
        config: Server configuration.
        reload: Whether to enable auto-reload on code changes.
    """
    logger.info(
        f"Starting server for: {config.name}"
        f"{' (reload enabled)' if reload else ''}"
    )

    # Set module-level config for factory function
    global _reload_config
    _reload_config = config

    # Use factory mode with import string (required for reload)
    uvicorn.run(
        "qtype.commands.serve:create_api_app",
        factory=True,
        host=config.host,
        port=config.port,
        log_level="info",
        reload=reload,
        reload_includes=[
            str(config.spec_path)
        ],  # Watch the spec file for changes
    )


def serve(args: argparse.Namespace) -> None:
    """Run a QType YAML spec file as an API.

    Args:
        args: Arguments passed from the command line.
    """
    config = ServerConfig.from_args(args)
    _run_server(config, reload=args.reload)


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
    cmd_parser.add_argument(
        "--reload",
        action="store_true",
        help="Enable auto-reload on code changes (default: False).",
    )
    cmd_parser.set_defaults(func=serve)

    cmd_parser.add_argument(
        "spec", type=str, help="Path to the QType YAML spec file."
    )
