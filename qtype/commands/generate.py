import argparse
import json
import logging
from typing import Optional

from qtype.commons.generate import dump_commons_library
from qtype.dsl.model import Document

logger = logging.getLogger(__name__)

def generate_schema(args: argparse.Namespace) -> None:
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
        logger.info(f"Schema written to {output_path}")
    else:
        logger.info("Schema is:\n%s", output)

def parser(subparsers: argparse._SubParsersAction) -> None:
    """Set up the generate subcommand parser."""
    cmd_parser = subparsers.add_parser(
        "generate", help="Generates qtype files from different sources."
    )
    generate_subparsers = cmd_parser.add_subparsers(
        dest="generate_target", required=True
    )

    # Parse for generating commons library tools
    commons_parser = generate_subparsers.add_parser(
        "commons", help="Generates the commons library tools."
    )
    commons_parser.add_argument(
        "-p",
        "--prefix",
        type=str,
        default="./common/",
        help="Output prefix for the YAML file (default: ./common/)",
    )
    commons_parser.set_defaults(func=dump_commons_library)

    # Parser for generating the json schema
    schema_parser = generate_subparsers.add_parser(
        "schema", help="Generates the schema for the QType DSL."
    )
    schema_parser.add_argument(
        "-o",
        "--output",
        type=str,
        help="Output file for the schema (default: stdout)",
    )
    schema_parser.set_defaults(func=generate_schema)
