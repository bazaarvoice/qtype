import argparse
import json
from typing import Optional

from qtype.dsl.model import Document


def setup_generate_schema_parser(subparsers: argparse._SubParsersAction) -> None:
    """Set up the generate-schema subcommand parser.

    Args:
        subparsers: The subparsers object to add the command to.
    """
    parser = subparsers.add_parser(
        "generate-schema", help="Generate a JSON schema for QType specs."
    )
    parser.add_argument(
        "-o",
        "--output",
        type=str,
        help="Output file for the schema (default: stdout)",
    )
    parser.set_defaults(func=generate_schema_main)


def generate_schema_main(args: argparse.Namespace) -> None:
    """Generate and output the JSON schema for Document.

    Args:
        args (argparse.Namespace): Command-line arguments with an optional
            'output' attribute specifying the output file path.
    """
    schema = Document.model_json_schema()
    # Add the $schema property to indicate JSON Schema version
    schema["$schema"] = "http://json-schema.org/draft-07/schema#"
    output = json.dumps(schema, indent=2)
    output_path: Optional[str] = getattr(args, "output", None)
    if output_path:
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(output)
    else:
        print(output)
