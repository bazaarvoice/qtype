import argparse
import json
import logging
from pathlib import Path
from typing import Any, Optional

from qtype.dsl.model import Document

logger = logging.getLogger(__name__)


def generate_aws_bedrock_models() -> list[dict[str, Any]]:
    """Generate AWS Bedrock model definitions.

    Returns:
        List of model definitions for AWS Bedrock models.

    Raises:
        ImportError: If boto3 is not installed.
        Exception: If AWS API call fails.
    """
    import boto3  # type: ignore[import-untyped]

    logger.info("Discovering AWS Bedrock models...")
    client = boto3.client("bedrock")
    models = client.list_foundation_models()

    model_definitions = []
    for model_summary in models.get("modelSummaries", []):
        model_definitions.append(
            {
                "id": model_summary["modelId"],
                "provider": "aws-bedrock",
            }
        )

    logger.info(f"Discovered {len(model_definitions)} AWS Bedrock models")
    return model_definitions


def run_dump_commons_library(args: argparse.Namespace) -> None:
    """Generate commons library tools and AWS Bedrock models."""
    from pathlib import Path

    from qtype.dsl.model import Model, ModelList

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
            model_definitions = generate_aws_bedrock_models()

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
            from pydantic_yaml import to_yaml_str

            content = to_yaml_str(
                model_list, exclude_none=True, exclude_unset=True
            )
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


def _copy_resource_file(resource, rel_path: Path, output_file: Path) -> None:
    """Copy a file from a resource directory to an output location."""
    content = resource.get_file(str(rel_path))
    output_file.parent.mkdir(parents=True, exist_ok=True)
    output_file.write_text(content, encoding="utf-8")


def run_generate_skill(args: argparse.Namespace) -> None:
    """Generate a Claude skill with QType documentation and examples.

    Args:
        args: Command-line arguments with 'output' path.
    """
    from qtype.mcp.server import _docs_resource, _examples_resource

    output_path = Path(args.output) / "qtype-architect"

    # Copy skill documentation files
    skills_path = _docs_resource.get_path() / "skills" / "architect"
    skill_count = 0
    for skill_file in skills_path.rglob("*.*"):
        rel_path = skill_file.relative_to(_docs_resource.get_path())
        _copy_resource_file(
            _docs_resource,
            rel_path,
            output_path / rel_path.relative_to("skills/architect"),
        )
        skill_count += 1

    # Copy all example files
    example_count = 0
    for yaml_file in _examples_resource.get_path().rglob("*.yaml"):
        rel_path = yaml_file.relative_to(_examples_resource.get_path())
        if "legacy" not in rel_path.parts:
            _copy_resource_file(
                _examples_resource, rel_path, output_path / "assets" / rel_path
            )
            example_count += 1

    logger.info(
        f"Skill generated at {output_path}: "
        f"{skill_count} docs, {example_count} examples"
    )


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
        "pattern": "^.*\\$\\{[^}:]+(?::-[^}]*)?\\}.*$",
        "description": "String with environment variable substitution using ${VAR_NAME} or ${VAR_NAME:-default} syntax",
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

    # Parser for generating Agent skills
    skill_parser = generate_subparsers.add_parser(
        "skills",
        help="Generates Agent skills with QType documentation and examples.",
    )
    skill_parser.add_argument(
        "-o",
        "--output",
        type=str,
        default=".claude/skills",
        help="Output directory for the skills (default: .claude/skills)",
    )
    skill_parser.set_defaults(func=run_generate_skill)

    # Parser for generating the semantic model
    # only add this if networkx and ruff are installed
    try:
        import networkx  # noqa: F401
        import ruff  # type: ignore[import-untyped]  # noqa: F401

        has_semantic_deps = True
    except ImportError:
        logger.debug(
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
