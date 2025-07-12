import argparse
import logging
from qtype.semantic.tool_provider_python_module import load_python_module_tools
from qtype.dsl.model import PythonModuleToolProvider, ToolList
from pydantic_yaml import to_yaml_str

logger = logging.getLogger(__name__)


def dump_commons_library(args: argparse.Namespace) -> None:
    provider = PythonModuleToolProvider(
        module_path="qtype.commons.tools", id="qtype.commons.tools"
    )
    tools = load_python_module_tools(provider)
    if not tools:
        logger.error("No tools found in the commons library.")
        return

    tool_list = ToolList(root=tools)  # type: ignore
    result = to_yaml_str(tool_list)
    logging.info("Result:\n %s", result)


def parser(subparsers: argparse._SubParsersAction) -> None:
    """Set up the commons library subcommand parser."""
    cmd_parser = subparsers.add_parser(
        "commons", help="Export commons library."
    )
    cmd_parser.add_argument(
        "-o",
        "--output",
        type=str,
        help="Output file for the schema (default: stdout)",
    )
    cmd_parser.set_defaults(func=dump_commons_library)
