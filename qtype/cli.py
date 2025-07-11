"""
QType CLI entry point for generating schemas and validating QType specs.
"""

import argparse
import logging

from .commands import generate_schema_main, validate_main
# , run_main, validate_main


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

    # generate-schema subcommand
    gen_parser = subparsers.add_parser(
        "generate-schema", help="Generate a JSON schema for QType specs."
    )
    gen_parser.add_argument(
        "-o",
        "--output",
        type=str,
        help="Output file for the schema (default: stdout)",
    )
    gen_parser.set_defaults(func=generate_schema_main)

    # validate subcommand
    val_parser = subparsers.add_parser(
        "validate", help="Validate a QType YAML spec against the schema."
    )
    val_parser.add_argument(
        "spec", type=str, help="Path to the QType YAML spec file."
    )
    val_parser.add_argument(
        "-p", "--print", action="store_true",
        help="Print the spec after validation (default: False)",
    )
    val_parser.set_defaults(func=validate_main)

    # # run subcommand
    # run_parser = subparsers.add_parser(
    #     "run", help="Run a QType YAML spec by executing its flows."
    # )
    # run_parser.add_argument(
    #     "spec", type=str, help="Path to the QType YAML spec file."
    # )
    # run_parser.set_defaults(func=run_main)

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
