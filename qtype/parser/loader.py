"""
YAML loading and validation with environment variable support.
"""

from __future__ import annotations

import os
import re
from typing import Any, Dict

import yaml
from dotenv import load_dotenv


class EnvVarLoader(yaml.SafeLoader):
    """
    YAML loader that supports environment variable substitution.

    Supports the following syntax:
    - ${VAR_NAME} - Required environment variable (raises error if not found)
    - ${VAR_NAME:default_value} - Optional with default value
    """

    pass


def env_var_constructor(loader: EnvVarLoader, node: yaml.ScalarNode) -> str:
    """
    Constructor for environment variable substitution.

    Args:
        loader: The YAML loader instance.
        node: The YAML node containing the environment variable reference.

    Returns:
        The resolved environment variable value.

    Raises:
        ValueError: If a required environment variable is not found.
    """
    value = loader.construct_scalar(node)

    # Pattern to match ${VAR_NAME} or ${VAR_NAME:default}
    pattern = r"\$\{([^}:]+)(?::([^}]*))?\}"

    def replace_env_var(match: re.Match[str]) -> str:
        var_name = match.group(1)
        default_value = match.group(2)

        env_value = os.getenv(var_name)

        if env_value is not None:
            return env_value
        elif default_value is not None:
            return default_value
        else:
            raise ValueError(
                f"Environment variable '{var_name}' is required but not set"
            )

    return re.sub(pattern, replace_env_var, value)


# Add the constructor for environment variable pattern
EnvVarLoader.add_constructor("tag:yaml.org,2002:str", env_var_constructor)


def load_yaml_with_env_vars(file_path: str) -> Dict[str, Any]:
    """
    Load a YAML file with environment variable substitution support.

    Automatically loads .env files from the current directory and the
    directory containing the YAML file.

    Args:
        file_path: Path to the YAML file to load.

    Returns:
        The parsed YAML data with environment variables resolved.

    Raises:
        ValueError: If a required environment variable is not found.
        FileNotFoundError: If the YAML file doesn't exist.
        yaml.YAMLError: If the YAML file is malformed.
    """
    # Load .env files in order of precedence:
    # 1. .env in the directory containing the YAML file
    # 2. .env in the current working directory
    yaml_dir = os.path.dirname(os.path.abspath(file_path))
    yaml_env_file = os.path.join(yaml_dir, ".env")
    cwd_env_file = os.path.join(os.getcwd(), ".env")

    # Load .env from YAML directory first (lower precedence)
    if os.path.exists(yaml_env_file):
        load_dotenv(yaml_env_file)

    # Load .env from current directory (higher precedence)
    if os.path.exists(cwd_env_file) and cwd_env_file != yaml_env_file:
        load_dotenv(cwd_env_file)

    with open(file_path, "r", encoding="utf-8") as f:
        result = yaml.load(f, Loader=EnvVarLoader)
        return result if result is not None else {}
