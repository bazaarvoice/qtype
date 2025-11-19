"""
QType CLI entry point for generating schemas and validating QType specs.
"""

import argparse
import importlib
import logging
from pathlib import Path

from qtype.base.logging import get_logger

logger = get_logger("application.facade")

try:
    from importlib.metadata import entry_points
except ImportError:
    # Fallback for Python < 3.10 (though you require 3.10+)
    from importlib_metadata import entry_points  # type: ignore[no-redef]


def _discover_commands(subparsers: argparse._SubParsersAction) -> None:
    """Automatically discover and register command modules.

    This function discovers commands from two sources:
    1. Built-in commands from the local commands directory
    2. Plugin commands from entry points defined by third-party packages

    Args:
        subparsers: The subparsers object to add commands to.
    """
    # First, discover built-in commands from the local commands directory
    _discover_local_commands(subparsers)

    # Then, discover plugin commands from entry points
    _discover_plugin_commands(subparsers)


def _discover_local_commands(subparsers: argparse._SubParsersAction) -> None:
    """Discover and register built-in command modules from the local commands directory.

    Args:
        subparsers: The subparsers object to add commands to.
    """
    commands_dir = Path(__file__).parent / "commands"

    for py_file in commands_dir.glob("*.py"):
        # Skip __init__.py and other private files
        if py_file.name.startswith("_"):
            continue

        module_name = f"qtype.commands.{py_file.stem}"
        try:
            module = importlib.import_module(module_name)
            # Call the parser function to set up the subparser
            if hasattr(module, "parser"):
                module.parser(subparsers)
            else:
                logging.warning(
                    f"Built-in command module {module_name} does not have a 'parser' function"
                )
        except Exception as e:
            logging.error(
                f"Failed to load built-in command module {module_name}: {e}",
                exc_info=True,
            )


def _discover_plugin_commands(subparsers: argparse._SubParsersAction) -> None:
    """Discover and register plugin command modules from entry points.

    Third-party packages can register commands by defining entry points in their
    setup.py or pyproject.toml file like this:

    [project.entry-points."qtype.commands"]
    my-command = "my_package.qtype_commands:my_command_parser"

    Args:
        subparsers: The subparsers object to add commands to.
    """
    try:
        # Get all entry points for the 'qtype.commands' group
        eps = entry_points(group="qtype.commands")

        for entry_point in eps:
            try:
                # Load the parser function from the entry point
                parser_func = entry_point.load()

                # Call the parser function to set up the subparser
                if callable(parser_func):
                    parser_func(subparsers)
                    logging.debug(
                        f"Successfully loaded plugin command '{entry_point.name}' "
                        f"from {entry_point.value}"
                    )
                else:
                    logging.warning(
                        f"Plugin entry point '{entry_point.name}' "
                        f"({entry_point.value}) is not callable"
                    )
            except Exception as e:
                logging.error(
                    f"Failed to load plugin command '{entry_point.name}' "
                    f"from {entry_point.value}: {e}",
                    exc_info=True,
                )
    except Exception as e:
        logging.error(
            f"Failed to discover plugin commands: {e}",
            exc_info=True,
        )


def main() -> None:
    """
    Main entry point for the QType CLI.
    Sets up argument parsing and dispatches to the appropriate subcommand.
    """
    parser = argparse.ArgumentParser(
        description="QType CLI: Generate schema, validate, or run QType specs."
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="Set the logging level (default: INFO)",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Auto-discover and register commands
    _discover_commands(subparsers)

    args = parser.parse_args()

    # Set logging level based on user input
    logging.basicConfig(
        level=getattr(logging, args.log_level),
        format="%(levelname)s: %(message)s",
    )

    # Dispatch to the selected subcommand
    args.func(args)


if __name__ == "__main__":
    main()
