"""
YAML loading and validation with environment variable support and file inclusion.
"""

from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Any, Dict
from urllib.parse import urljoin, urlparse

import fsspec
import yaml
from dotenv import load_dotenv


class YamlLoader(yaml.SafeLoader):
    """
    YAML loader that supports environment variable substitution and file inclusion.

    Supports the following syntax:
    - ${VAR_NAME} - Required environment variable (raises error if not found)
    - ${VAR_NAME:default_value} - Optional with default value
    - !include path/to/file.yaml - Include external YAML file
    - !include_raw path/to/file.txt - Include raw text file as string

    File paths can be:
    - Local filesystem paths (relative or absolute)
    - URLs (http://, https://)
    - GitHub URLs (github://)
    - S3 URLs (s3://)
    - Any fsspec-supported protocol
    """

    def __init__(self, stream: Any) -> None:
        super().__init__(stream)
        # Store the base path/URL of the current file for relative path resolution
        if hasattr(stream, "name"):
            self._current_path = stream.name
        else:
            self._current_path = str(Path.cwd())


def _env_var_constructor(loader: YamlLoader, node: yaml.ScalarNode) -> str:
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
            msg = f"Environment variable '{var_name}' is required but not set"
            raise ValueError(msg)

    return re.sub(pattern, replace_env_var, value)


def _include_file_constructor(loader: YamlLoader, node: yaml.ScalarNode) -> Any:
    """
    Constructor for !include tag to load external YAML files using fsspec.

    Args:
        loader: The YAML loader instance.
        node: The YAML node containing the file path/URL.

    Returns:
        The parsed YAML data from the included file.

    Raises:
        FileNotFoundError: If the included file doesn't exist.
        yaml.YAMLError: If the included file is malformed YAML.
    """
    file_path = loader.construct_scalar(node)

    # Resolve relative paths/URLs relative to the current file
    resolved_path = _resolve_path(loader._current_path, file_path)

    try:
        with fsspec.open(resolved_path, "r", encoding="utf-8") as f:
            content = f.read()  # type: ignore[misc]

            # Create a mock stream with the resolved path for nested includes
            class IncludeStream:
                def __init__(self, content: str, name: str) -> None:
                    self.content = content
                    self.name = name
                    self._pos = 0

                def read(self, size: int = -1) -> str:
                    if size == -1:
                        result = self.content[self._pos:]
                        self._pos = len(self.content)
                    else:
                        result = self.content[self._pos:self._pos + size]
                        self._pos += len(result)
                    return result

            stream = IncludeStream(content, resolved_path)
            return yaml.load(stream, Loader=YamlLoader)
    except ValueError:
        # Re-raise ValueError (e.g., missing environment variables) without wrapping
        raise
    except Exception as e:
        msg = f"Failed to load included file '{resolved_path}': {e}"
        raise FileNotFoundError(msg) from e


def _include_raw_constructor(loader: YamlLoader, node: yaml.ScalarNode) -> str:
    """
    Constructor for !include_raw tag to load external text files using fsspec.

    Args:
        loader: The YAML loader instance.
        node: The YAML node containing the file path/URL.

    Returns:
        The raw text content of the included file.

    Raises:
        FileNotFoundError: If the included file doesn't exist.
    """
    file_path = loader.construct_scalar(node)

    # Resolve relative paths/URLs relative to the current file
    resolved_path = _resolve_path(loader._current_path, file_path)

    try:
        with fsspec.open(resolved_path, "r", encoding="utf-8") as f:
            return f.read()  # type: ignore[misc]
    except Exception as e:
        msg = f"Failed to load included file '{resolved_path}': {e}"
        raise FileNotFoundError(msg) from e


def _resolve_path(current_path: str, target_path: str) -> str:
    """
    Resolve a target path relative to the current file path.

    Args:
        current_path: The path/URL of the current file.
        target_path: The target path/URL to resolve.

    Returns:
        The resolved absolute path/URL.
    """
    # If target is already absolute (has scheme or starts with /), use as-is
    parsed_target = urlparse(target_path)
    if parsed_target.scheme or target_path.startswith('/'):
        return target_path

    # Check if current path is a URL
    parsed_current = urlparse(current_path)
    if parsed_current.scheme:
        # Current is a URL, use urljoin for proper URL resolution
        return urljoin(current_path, target_path)
    else:
        # Current is a local path, resolve relative to its directory
        current_dir = Path(current_path).parent
        return str(current_dir / target_path)


def _load_env_files(file_path: str) -> None:
    """Load .env files in order of precedence."""
    # Only load .env files for local file paths, not URLs
    parsed = urlparse(file_path)
    if parsed.scheme:
        return  # Skip .env loading for URLs

    # Load .env files in order of precedence:
    # 1. .env in the directory containing the YAML file
    # 2. .env in the current working directory
    yaml_dir = Path(file_path).parent.resolve()
    yaml_env_file = yaml_dir / ".env"
    cwd_env_file = Path.cwd() / ".env"

    # Load .env from YAML directory first (lower precedence)
    if yaml_env_file.exists():
        load_dotenv(yaml_env_file)

    # Load .env from current directory (higher precedence)
    if cwd_env_file.exists() and cwd_env_file != yaml_env_file:
        load_dotenv(cwd_env_file)


# Register constructors for YamlLoader
YamlLoader.add_constructor("tag:yaml.org,2002:str", _env_var_constructor)
YamlLoader.add_constructor("!include", _include_file_constructor)
YamlLoader.add_constructor("!include_raw", _include_raw_constructor)


def load_yaml(file_path: str) -> Dict[str, Any]:
    """
    Load a YAML file with environment variable substitution and file inclusion support.

    Automatically loads .env files from the current directory and the
    directory containing the YAML file (for local files only).

    Args:
        file_path: Path or URL to the YAML file to load.

    Returns:
        The parsed YAML data with includes resolved and environment variables substituted.

    Raises:
        ValueError: If a required environment variable is not found.
        FileNotFoundError: If the YAML file or included files don't exist.
        yaml.YAMLError: If the YAML file is malformed.
    """
    _load_env_files(file_path)

    # Use fsspec to open the file, supporting URLs and various protocols
    with fsspec.open(file_path, "r", encoding="utf-8") as f:
        content = f.read()  # type: ignore[misc]

        # Create a mock stream with the file path as name for the loader
        class MockStream:
            def __init__(self, content: str, name: str) -> None:
                self.content = content
                self.name = name
                self._pos = 0

            def read(self, size: int = -1) -> str:
                if size == -1:
                    result = self.content[self._pos:]
                    self._pos = len(self.content)
                else:
                    result = self.content[self._pos:self._pos + size]
                    self._pos += len(result)
                return result

        mock_stream = MockStream(content, file_path)
        # Use the mock stream directly with the loader
        result = yaml.load(mock_stream, Loader=YamlLoader)
        return result if result is not None else {}
