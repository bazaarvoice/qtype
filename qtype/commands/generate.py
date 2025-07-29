import argparse
import json
import logging
from pathlib import Path
from typing import Optional

from qtype.commons.generate import dump_commons_library
from qtype.dsl.document import generate_documentation
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

    # Parser for generating the DSL documentation
    dsl_parser = generate_subparsers.add_parser(
        "dsl-docs",
        help="Generates markdown documentation for the QType DSL classes.",
    )
    dsl_parser.add_argument(
        "-o",
        "--output",
        type=str,
        default="docs/DSL-Reference/",
        help="Output directory for the DSL documentation (default: docs/DSL-Reference/)",
    )
    dsl_parser.set_defaults(
        func=lambda args: generate_documentation(Path(args.output))
    )

    # Parser for generating the semantic model
    # only add this if networkx and ruff are installed
    try:
        import networkx  # noqa: F401
        import ruff  # noqa: F401

        from qtype.semantic.generate import generate_semantic_model

        semantic_parser = generate_subparsers.add_parser(
            "semantic-model",
            help="Generates the semantic model (i.e., qtype/semantic/model.py) from QType DSL.",
        )
        semantic_parser.add_argument(
            "-o",
            "--output",
            type=str,
            default="qtype/semantic/model.py",
            help="Output file for the semantic model (default: stdout)",
        )
        semantic_parser.set_defaults(func=generate_semantic_model)
    except ImportError:
        logger.debug(
            "NetworkX or Ruff is not installed. Skipping semantic model generation."
        )
