import argparse
import sys
from .commands.generate_schema import generate_schema_main
from .commands.validate import validate_main

def main():
    parser = argparse.ArgumentParser(
        description="QType CLI: Generate schema or validate QType specs."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # generate_schema subcommand
    gen_parser = subparsers.add_parser(
        "generate-schema", help="Generate a JSON schema for QType specs."
    )
    gen_parser.add_argument(
        "-o", "--output", type=str, help="Output file for the schema (default: stdout)"
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
        "--schema", type=str, help="Path to the schema file (optional)."
    )
    val_parser.set_defaults(func=validate_main)

    args = parser.parse_args()
    args.func(args)

if __name__ == "__main__":
    main()