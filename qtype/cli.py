"""
QType CLI entry point for generating schemas and validating QType specs.
"""

import argparse
import logging

from .commands import (
    setup_generate_schema_parser,
    setup_run_parser,
    setup_validate_parser,
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

    # Set up subcommands using their respective setup functions
    setup_generate_schema_parser(subparsers)
    setup_validate_parser(subparsers)
    setup_run_parser(subparsers)

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
