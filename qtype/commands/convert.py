import argparse
import logging

from pydantic_yaml import to_yaml_str

from qtype.commons.generate import _write_yaml_file
from qtype.converters.tools_from_module import tools_from_module
from qtype.dsl.model import ToolList

logger = logging.getLogger(__name__)


def convert_api(args: argparse.Namespace) -> None:
    raise NotImplementedError("API conversion is not implemented yet.")


def convert_module(args: argparse.Namespace) -> None:
    """Convert Python module tools to qtype format."""
    tools = ToolList(tools_from_module(args.module_path))  # type: ignore
    if not tools:
        raise ValueError(f"No tools found in the module: {args.module_path}")

    if args.output:
        _write_yaml_file(tools, args.output)
        logger.info("Resulting yaml written to %s", args.output)
    else:
        logger.info(
            "Resulting yaml:\n%s",
            to_yaml_str(tools, exclude_unset=True, exclude_none=True),
        )


def parser(subparsers: argparse._SubParsersAction) -> None:
    """Set up the converter subcommand parser."""
    cmd_parser = subparsers.add_parser(
        "convert", help="Creates qtype files from different sources."
    )

    # Create a new subparser for "convert api", "convert module", etc.
    convert_subparsers = cmd_parser.add_subparsers(
        dest="convert_command", required=True
    )

    convert_module_parser = convert_subparsers.add_parser(
        "module", help="Converts module specifications to qtype format."
    )
    convert_module_parser.add_argument(
        "module_path",
        type=str,
        help="Path to the Python module to convert.",
    )
    convert_module_parser.add_argument(
        "-o",
        "--output",
        type=str,
        default=None,
        help="Where to save the converted YAML file. If not specified, it is just printed to stdout.",
    )
    convert_module_parser.set_defaults(func=convert_module)

    convert_api_parser = convert_subparsers.add_parser(
        "api", help="Converts API specifications to qtype format."
    )
    convert_api_parser.add_argument(
        "openapi_spec",
        type=str,
        help="URL of the OpenAPI specification.",
    )
    convert_api_parser.add_argument(
        "-o",
        "--output",
        type=str,
        default=None,
        help="Where to save the converted YAML file. If not specified, it is just printed to stdout.",
    )
    convert_api_parser.set_defaults(func=convert_api)
