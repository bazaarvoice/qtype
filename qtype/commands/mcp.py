"""
Command-line interface for starting the QType MCP server.
"""

from __future__ import annotations

import argparse
import logging
from typing import Any

from qtype.mcp.server import mcp

logger = logging.getLogger(__name__)


def main(args: Any) -> None:
    """
    Start the QType MCP server with the specified transport.

    Args:
        args: Arguments passed from the command line or calling context.
    """

    # Update server settings with CLI arguments
    mcp.settings.host = args.host
    mcp.settings.port = args.port

    logger.info(f"Starting QType MCP server with {args.transport} transport")

    if args.transport in ("sse", "streamable-http"):
        logger.info(f"Server will be available at {args.host}:{args.port}")

    # Run the server with the specified transport
    mcp.run(transport=args.transport)


def parser(subparsers: argparse._SubParsersAction) -> None:
    """Set up the mcp subcommand parser.

    Args:
        subparsers: The subparsers object to add the command to.
    """
    cmd_parser = subparsers.add_parser(
        "mcp",
        help="Start the QType MCP server for AI agent integration.",
    )
    cmd_parser.add_argument(
        "-t",
        "--transport",
        type=str,
        choices=["stdio", "sse", "streamable-http"],
        default="stdio",
        help="Transport protocol to use (default: stdio)",
    )
    cmd_parser.add_argument(
        "--host",
        type=str,
        default="0.0.0.0",
        help="Host to bind to for HTTP/SSE transports (default: 0.0.0.0)",
    )
    cmd_parser.add_argument(
        "-p",
        "--port",
        type=int,
        default=8000,
        help="Port to bind to for HTTP/SSE transports (default: 8000)",
    )
    cmd_parser.set_defaults(func=main)
