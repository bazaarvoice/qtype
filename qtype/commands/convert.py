"""
Command-line interface for converting tools and APIs to qtype format.
"""

from __future__ import annotations

import argparse
import logging
from pathlib import Path

from qtype.dsl.model import Application, Document, ToolList

logger = logging.getLogger(__name__)


def _convert_to_yaml(doc: Application | ToolList) -> str:
    """Convert a document to YAML format."""
    from pydantic_yaml import to_yaml_str

    # Wrap in Document if needed
    if isinstance(doc, Application):
        wrapped = Document(root=doc)
    else:
        wrapped = doc

    # NOTE: We use exclude_none but NOT exclude_unset because discriminator
    # fields like 'type' have default values and must be included in output
    return to_yaml_str(wrapped, exclude_none=True)


def convert_api(args: argparse.Namespace) -> None:
    """Convert API specification to qtype format."""
    from qtype.application.converters.tools_from_api import tools_from_api

    try:
        api_name, auths, tools, types = tools_from_api(args.api_spec)
        if not tools:
            raise ValueError(
                f"No tools found from the API specification: {args.api_spec}"
            )
        if not auths and not types:
            doc = ToolList(
                root=list(tools),
            )
        else:
            doc: Application | ToolList = Application(
                id=api_name,
                description=f"Tools created from API specification {args.api_spec}",
                tools=list(tools),
                types=types,
                auths=auths,
            )
        # Convert to YAML format
        content = _convert_to_yaml(doc)

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


def convert_module(args: argparse.Namespace) -> None:
    """Convert Python module tools to qtype format."""
    from qtype.application.converters.tools_from_module import (
        tools_from_module,
    )

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

        # Convert to YAML format
        content = _convert_to_yaml(doc)

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
