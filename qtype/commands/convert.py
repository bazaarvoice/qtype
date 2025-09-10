"""
Command-line interface for converting tools and APIs to qtype format.
"""

from __future__ import annotations

import argparse
import logging
from pathlib import Path

from qtype.application.facade import QTypeFacade

logger = logging.getLogger(__name__)


def convert_api(args: argparse.Namespace) -> None:
    """Convert API specification to qtype format."""
    raise NotImplementedError("API conversion is not implemented yet.")


def convert_module(args: argparse.Namespace) -> None:
    """Convert Python module tools to qtype format."""
    from qtype.application.converters.tools_from_module import (
        tools_from_module,
    )
    from qtype.dsl.model import Application, ToolList

    try:
        tools, types = tools_from_module(args.module_path)
        if not tools:
            raise ValueError(
                f"No tools found in the module: {args.module_path}"
            )

        # Create application document
        if types:
            doc: Application | ToolList = Application(
                id=args.module_path,
                description=f"Tools created from Python module {args.module_path}",
                tools=list(tools),
                types=types,
            )
        else:
            doc = ToolList(
                root=list(tools),
            )

        # Use facade to convert to YAML format
        facade = QTypeFacade()
        content = facade.convert_document(doc)

        # Write to file or stdout
        if args.output:
            output_path = Path(args.output)
            output_path.write_text(content, encoding="utf-8")
            logger.info(f"✅ Converted tools saved to {output_path}")
        else:
            print(content)

    except Exception as e:
        logger.error(f"❌ Conversion failed: {e}")
        raise


def parser(subparsers: argparse._SubParsersAction) -> None:
    """Set up the converter subcommand parser."""
    cmd_parser = subparsers.add_parser(
        "convert", help="Creates qtype files from different sources."
    )

    # Create a new subparser for "convert api", "convert module", etc.
    convert_subparsers = cmd_parser.add_subparsers(
        dest="convert_command", required=True
    )

    # Convert from Python module
    module_parser = convert_subparsers.add_parser(
        "module", help="Convert a Python module to qtype tools format."
    )
    module_parser.add_argument(
        "module_path", type=str, help="Path to the Python module to convert."
    )
    module_parser.add_argument(
        "-o",
        "--output",
        type=str,
        help="Output file path. If not specified, prints to stdout.",
    )
    module_parser.set_defaults(func=convert_module)

    # Convert from API specification
    api_parser = convert_subparsers.add_parser(
        "api", help="Convert an API specification to qtype format."
    )
    api_parser.add_argument(
        "api_spec", type=str, help="Path to the API specification file."
    )
    api_parser.add_argument(
        "-o",
        "--output",
        type=str,
        help="Output file path. If not specified, prints to stdout.",
    )
    api_parser.set_defaults(func=convert_api)
