import argparse
import json
import logging
from pathlib import Path
from typing import Optional

from qtype.dsl.model import Document

logger = logging.getLogger(__name__)


def run_dump_commons_library(args: argparse.Namespace) -> None:
    """Generate commons library tools and AWS Bedrock models."""
    import logging
    from pathlib import Path

    from qtype.application.facade import QTypeFacade
    from qtype.dsl.model import Model, ModelList

    logger = logging.getLogger(__name__)
    facade = QTypeFacade()

    try:
        # Generate common tools using convert module functionality
        logger.info("Generating common tools...")

        # Create a mock args object for convert_module
        import argparse

        from qtype.commands.convert import convert_module

        convert_args = argparse.Namespace(
            module_path="qtype.application.commons.tools",
            output=f"{args.prefix}/tools.qtype.yaml",
        )
        convert_module(convert_args)

        # Generate AWS Bedrock models
        logger.info("Generating AWS Bedrock models...")
        try:
            model_definitions = facade.generate_aws_bedrock_models()

            model_list = ModelList(
                root=[
                    Model(
                        id=model_def["id"],
                        provider=model_def["provider"],
                    )
                    for model_def in model_definitions
                ]
            )

            # Convert to YAML and save
            content = facade.convert_document(model_list)
            output_path = Path(f"{args.prefix}/aws.bedrock.models.qtype.yaml")
            output_path.write_text(content, encoding="utf-8")
            logger.info(f"AWS Bedrock models exported to {output_path}")

        except ImportError:
            logger.warning(
                "boto3 not available. Skipping AWS Bedrock model generation."
            )
        except Exception as e:
            logger.error(f"Failed to generate AWS Bedrock models: {e}")

        logger.info("Commons library generation complete.")

    except Exception as e:
        logger.error(f"Failed to generate commons library: {e}")
        raise


def run_generate_documentation(args: argparse.Namespace) -> None:
    from qtype.application.documentation import generate_documentation

    generate_documentation(Path(args.output))


def generate_schema(args: argparse.Namespace) -> None:
    """Generate and output the JSON schema for Document.

    Args:
        args (argparse.Namespace): Command-line arguments with an optional
            'output' attribute specifying the output file path.
    """
    schema = Document.model_json_schema()

    # Add the $schema property to indicate JSON Schema version
    schema["$schema"] = "http://json-schema.org/draft-07/schema#"

    # Add custom YAML tag definitions for QType loader features
    if "$defs" not in schema:
        schema["$defs"] = {}

    # Note: Custom YAML tags (!include, !include_raw) and environment variable
    # substitution (${VAR}) are handled by the QType YAML loader at parse time,
    # not by JSON Schema validation. We define them in $defs for documentation
    # purposes, but we don't apply them to string fields since:
    # 1. They would cause false positives (e.g., "localhost" matching as valid)
    # 2. The YAML loader processes these before schema validation occurs
    # 3. After YAML loading, the schema sees the resolved/substituted values
    #
    # Schema validation happens on the post-processed document structure,
    # so we don't need to (and shouldn't) validate the raw YAML tag syntax.

    # Define custom YAML tags used by QType loader
    schema["$defs"]["qtype_include_tag"] = {
        "type": "string",
        "pattern": "^!include\\s+.+",
        "description": "Include external YAML file using QType's !include tag",
    }

    schema["$defs"]["qtype_include_raw_tag"] = {
        "type": "string",
        "pattern": "^!include_raw\\s+.+",
        "description": "Include raw text file using QType's !include_raw tag",
    }

    schema["$defs"]["qtype_env_var"] = {
        "type": "string",
        "pattern": "^.*\\$\\{[^}:]+(?::[^}]*)?\\}.*$",
        "description": "String with environment variable substitution using ${VAR_NAME} or ${VAR_NAME:default} syntax",
    }

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
    commons_parser.set_defaults(func=run_dump_commons_library)

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
        default="docs/components/",
        help="Output directory for the DSL documentation (default: docs/components/)",
    )
    dsl_parser.set_defaults(func=run_generate_documentation)

    # Parser for generating the semantic model
    # only add this if networkx and ruff are installed
    try:
        import networkx  # noqa: F401
        import ruff  # type: ignore[import-untyped]  # noqa: F401

        has_semantic_deps = True
    except ImportError:
        logger.warning(
            "NetworkX or Ruff is not installed. Skipping semantic model generation."
        )
        has_semantic_deps = False

    if has_semantic_deps:
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
