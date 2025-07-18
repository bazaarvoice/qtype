"""
QType CLI entry point for generating schemas and validating QType specs.
"""

import argparse
import importlib
import logging
from pathlib import Path


def _discover_commands(subparsers: argparse._SubParsersAction) -> None:
    """Automatically discover and register command modules.

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
                    f"Command module {module_name} does not have a 'parser' function"
                )
        except Exception as e:
            logging.error(
                f"Failed to load command module {module_name}: {e}",
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
