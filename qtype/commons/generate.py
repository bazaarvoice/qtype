import argparse
import logging

from pydantic import BaseModel
from pydantic_yaml import to_yaml_str

from qtype.converters.tools_from_module import tools_from_module
from qtype.dsl.model import Model, ModelList, ToolList

logger = logging.getLogger(__name__)


def _write_yaml_file(data: BaseModel, output_path: str) -> None:
    """
    Write a Pydantic model to a YAML file.

    Args:
        data: The Pydantic model instance to write.
        output_path: The path where the YAML file will be saved.
    """
    result = to_yaml_str(data, exclude_unset=True, exclude_none=True)
    with open(output_path, "w") as f:
        f.write(result)
    logger.info(f"Data exported to {output_path}")


def dump_built_in_tools(args: argparse.Namespace) -> None:
    tools = tools_from_module("qtype.commons.tools")
    if not tools:
        logger.error("No tools found in the commons library.")
        return

    tool_list = ToolList(root=tools)  # type: ignore
    output_path = f"{args.prefix}/tools.qtype.yaml"
    _write_yaml_file(tool_list, output_path)
    logging.info(f"Built-in tools exported to {output_path}")


def dump_aws_bedrock_models(args: argparse.Namespace) -> None:
    """
    Export AWS Bedrock models to a YAML file.

    Args:
        args: Command line arguments containing the output prefix.
    """
    try:
        import boto3

        client = boto3.client("bedrock")
        models = client.list_foundation_models()

        # generate a model list from the AWS Bedrock models
        # the return type of list_foundation_models is

        model_list = ModelList(
            [
                Model(
                    id=model_summary["modelId"],
                    provider="aws-bedrock",
                )
                for model_summary in models.get("modelSummaries", [])
            ]
        )
        output_path = f"{args.prefix}/aws.bedrock.models.qtype.yaml"
        _write_yaml_file(model_list, output_path)
        logging.info(f"AWS Bedrock Models exported to {output_path}")

        logger.info("Exporting AWS Bedrock models...")
        # Placeholder for actual implementation
        # This function should gather AWS Bedrock models and export them similarly to dump_built_in_tools
        logger.info("AWS Bedrock models exported successfully.")
    except ImportError:
        logger.error(
            "boto3 is not installed. Please install it to use AWS Bedrock model export."
        )


def dump_commons_library(args: argparse.Namespace) -> None:
    """
    Export the commons library tools to a YAML file.

    Args:
        args: Command line arguments containing the output prefix.
    """
    logger.info("Exporting commons library tools...")
    dump_built_in_tools(args)
    dump_aws_bedrock_models(args)
    logger.info("Commons library tools export complete.")
