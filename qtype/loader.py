"""
YAML loading and validation with environment variable support and file inclusion.
"""

from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Any
from urllib.parse import urljoin, urlparse

import fsspec
import yaml
from dotenv import load_dotenv
from fsspec.core import url_to_fs

from qtype.dsl import model as dsl
from qtype.dsl.validator import validate
from qtype.semantic.model import Application
from qtype.semantic.resolver import resolve


class _StringStream:
    """
    A file-like stream wrapper around string content for YAML loading.
    This class provides a readable stream interface that PyYAML can use
    to parse string content as if it were reading from a file.
    """

    def __init__(self, content: str, name: str | None = None) -> None:
        """
        Initialize the string stream.

        Args:
            content: The string content to wrap.
            name: Optional name/path for the stream (used for relative path resolution).
        """
        self.content = content
        self.name = name
        self._pos = 0

    def read(self, size: int = -1) -> str:
        """
        Read content from the stream.

        Args:
            size: Number of characters to read. If -1, read all remaining content.

        Returns:
            The requested content as a string.
        """
        if size == -1:
            result = self.content[self._pos :]
            self._pos = len(self.content)
        else:
            result = self.content[self._pos : self._pos + size]
            self._pos += len(result)
        return result


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
        if hasattr(stream, "name") and stream.name is not None:
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


def _include_file_constructor(
    loader: YamlLoader, node: yaml.ScalarNode
) -> Any:
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

            # Create a string stream with the resolved path for nested includes
            stream = _StringStream(content, resolved_path)
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
    if parsed_target.scheme or target_path.startswith("/"):
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


def _load_env_files(directories: list[Path]) -> None:
    """Load .env files from the specified directories."""
    for directory in directories:
        env_file = directory / ".env"
        if env_file.exists():
            load_dotenv(env_file)


# Register constructors for YamlLoader
YamlLoader.add_constructor("tag:yaml.org,2002:str", _env_var_constructor)
YamlLoader.add_constructor("!include", _include_file_constructor)
YamlLoader.add_constructor("!include_raw", _include_raw_constructor)


def load_yaml_from_string(
    content: str, original_uri: str | None = None
) -> dict[str, Any]:
    """
    Load a YAML file with environment variable substitution and file inclusion support.

    Args:
        content: The YAML content to load.

    Returns:
        The parsed YAML data with includes resolved and environment variables substituted.

    Raises:
        ValueError: If a required environment variable is not found.
        FileNotFoundError: If the YAML file or included files don't exist.
        yaml.YAMLError: If the YAML file is malformed.
    """

    # Create a string stream for the loader
    # Note: When loading from string, relative paths will be resolved relative to cwd
    stream = _StringStream(content, original_uri)
    # Use the string stream directly with the loader
    result = yaml.load(stream, Loader=YamlLoader)

    return result


def load_yaml(content: str) -> dict[str, Any]:
    """
    Load a YAML file with environment variable substitution and file inclusion support.

    Args:
        content: Either a fsspec uri/file path to load, or a string containing YAML content.

    Returns:
        The parsed YAML data with includes resolved and environment variables substituted.

    Raises:
        ValueError: If a required environment variable is not found.
        FileNotFoundError: If the YAML file or included files don't exist.
        yaml.YAMLError: If the YAML file is malformed.
    """
    try:
        # First check if content looks like a file path or URI
        if "\n" in content:
            # If it contains newlines, treat as raw YAML content
            is_uri = False
        else:
            # it has no new lines, so it's probably a uri
            # try to resolve it
            _ = url_to_fs(content)
            is_uri = True
    except (ValueError, OSError):
        is_uri = False

    # Load the environment variables from .env files
    directories = [Path.cwd()]

    if is_uri:
        # if the content is a uri, see if it is a local path. if it is, add the directory
        try:
            parsed = urlparse(content)
            if parsed.scheme in ["file", ""]:
                # For file-like URIs, resolve the path and add its directory
                directories.append(Path(parsed.path).parent)
        except Exception:
            pass

    # Load .env files from the specified directories
    _load_env_files(directories)

    # Load the yaml content
    if is_uri:
        original_uri = content
        with fsspec.open(content, "r", encoding="utf-8") as f:
            content = f.read()  # type: ignore[misc]
        return load_yaml_from_string(content, original_uri)
    else:
        return load_yaml_from_string(content)


ResolveableType = dsl.Agent | dsl.Application | dsl.Flow | list


def _resolve_root(doc: dsl.Document) -> ResolveableType:
    root = doc.root
    # If the docroot is a type that ends in the name `List`, resolve it again
    types_to_resolve = set(
        [
            dsl.AuthorizationProviderList,
            dsl.IndexList,
            dsl.ModelList,
            dsl.ToolList,
            dsl.VariableList,
        ]
    )
    if root is not None and type(root) in types_to_resolve:
        root = root.root  # type: ignore
    return root  # type: ignore[return-value]


def load(content: str) -> Application:
    """Load a QType YAML file, validate it, and return the resolved root."""
    yaml_data = load_yaml(content)
    document = dsl.Document.model_validate(yaml_data)
    document = _resolve_root(document)
    if not isinstance(document, dsl.Application):
        raise ValueError(
            f"Root document is not an Application, found {type(document)}."
        )
    document = validate(document)
    return resolve(document)
