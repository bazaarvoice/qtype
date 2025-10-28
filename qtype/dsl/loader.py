"""
YAML loading and validation with environment variable support and file inclusion.
"""

from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Any
from urllib.parse import urljoin, urlparse

import fsspec  # type: ignore[import-untyped]
import yaml
from dotenv import load_dotenv
from fsspec.core import url_to_fs  # type: ignore[import-untyped]

from qtype.base.types import CustomTypeRegistry
from qtype.dsl import model as dsl
from qtype.dsl.custom_types import build_dynamic_types


class YAMLLoadError(Exception):
    """Enhanced YAML loading error with line number information."""

    def __init__(
        self,
        message: str,
        line: int | None = None,
        column: int | None = None,
        source: str | None = None,
        original_error: Exception | None = None,
    ) -> None:
        self.message = message
        self.line = line
        self.column = column
        self.source = source
        self.original_error = original_error
        super().__init__(self._format_message())

    def _format_message(self) -> str:
        """Format the error message with location information."""
        parts = []
        if self.source:
            parts.append(f"in {self.source}")
        if self.line is not None:
            location = f"line {self.line + 1}"
            if self.column is not None:
                location += f", column {self.column + 1}"
            parts.append(location)

        if parts:
            return f"{self.message} ({', '.join(parts)})"
        return self.message


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


class _YamlLoader(yaml.SafeLoader):
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


class EnvVarHandler:
    """Handles environment variable substitution in YAML values."""

    @staticmethod
    def substitute(value: str) -> str:
        """
        Substitute environment variables in a string.

        Supports ${VAR_NAME} or ${VAR_NAME:default} syntax.

        Args:
            value: The string containing environment variable references

        Returns:
            String with environment variables substituted

        Raises:
            ValueError: If a required environment variable is not found
        """
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
                msg = (
                    f"Environment variable '{var_name}' is "
                    "required but not set"
                )
                raise ValueError(msg)

        return re.sub(pattern, replace_env_var, value)


class IncludeHandler:
    """Handles file inclusion in YAML documents."""

    @staticmethod
    def load_yaml_file(file_path: str, current_path: str) -> Any:
        """
        Load and parse a YAML file with environment variable substitution.

        Args:
            file_path: The file path/URL to load
            current_path: The current file path for relative resolution

        Returns:
            Parsed YAML data from the included file

        Raises:
            FileNotFoundError: If the included file doesn't exist
            yaml.YAMLError: If the included file is malformed YAML
        """
        resolved_path = _resolve_path(current_path, file_path)

        try:
            with fsspec.open(resolved_path, "r", encoding="utf-8") as f:
                content = f.read()  # type: ignore[misc]

                # Create a string stream with the resolved path for nested includes
                stream = _StringStream(content, resolved_path)
                return yaml.load(stream, Loader=_YamlLoader)
        except ValueError:
            # Re-raise ValueError (e.g., missing environment variables)
            raise
        except Exception as e:
            msg = f"Failed to load included file '{resolved_path}': {e}"
            raise FileNotFoundError(msg) from e

    @staticmethod
    def load_raw_file(file_path: str, current_path: str) -> str:
        """
        Load a raw text file.

        Args:
            file_path: The file path/URL to load
            current_path: The current file path for relative resolution

        Returns:
            Raw text content of the included file

        Raises:
            FileNotFoundError: If the included file doesn't exist
        """
        resolved_path = _resolve_path(current_path, file_path)

        try:
            with fsspec.open(resolved_path, "r", encoding="utf-8") as f:
                return f.read()  # type: ignore[no-any-return]
        except Exception as e:
            msg = f"Failed to load included file '{resolved_path}': {e}"
            raise FileNotFoundError(msg) from e


def _env_var_constructor(loader: _YamlLoader, node: yaml.ScalarNode) -> str:
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
    return EnvVarHandler.substitute(value)


def _include_file_constructor(
    loader: _YamlLoader, node: yaml.ScalarNode
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
    return IncludeHandler.load_yaml_file(file_path, loader._current_path)


def _include_raw_constructor(
    loader: _YamlLoader, node: yaml.ScalarNode
) -> str:
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
    return IncludeHandler.load_raw_file(file_path, loader._current_path)


class PathResolver:
    """Handles path resolution for different URI schemes and local paths."""

    @staticmethod
    def is_absolute(path: str) -> bool:
        """
        Check if a path is absolute.

        Args:
            path: The path to check

        Returns:
            True if the path is absolute (has scheme or starts with /)
        """
        parsed = urlparse(path)
        return bool(parsed.scheme) or path.startswith("/")

    @staticmethod
    def is_url(path: str) -> bool:
        """
        Check if a path is a URL.

        Args:
            path: The path to check

        Returns:
            True if the path has a URL scheme
        """
        parsed = urlparse(path)
        return bool(parsed.scheme)

    @staticmethod
    def resolve_url(base_url: str, target_path: str) -> str:
        """
        Resolve a target path relative to a base URL.

        Args:
            base_url: The base URL
            target_path: The target path to resolve

        Returns:
            The resolved URL
        """
        return urljoin(base_url, target_path)

    @staticmethod
    def resolve_local(base_path: str, target_path: str) -> str:
        """
        Resolve a target path relative to a local base path.

        Args:
            base_path: The base local path
            target_path: The target path to resolve

        Returns:
            The resolved local path
        """
        base_path_obj = Path(base_path)
        if base_path_obj.is_dir():
            base_dir = base_path_obj
        else:
            base_dir = base_path_obj.parent
        return str(base_dir / target_path)

    @classmethod
    def resolve(cls, current_path: str, target_path: str) -> str:
        """
        Resolve a target path relative to the current file path.

        Args:
            current_path: The path/URL of the current file
            target_path: The target path/URL to resolve

        Returns:
            The resolved absolute path/URL
        """
        # If target is already absolute, use as-is
        if cls.is_absolute(target_path):
            return target_path

        # Check if current path is a URL
        if cls.is_url(current_path):
            return cls.resolve_url(current_path, target_path)
        else:
            return cls.resolve_local(current_path, target_path)


def _resolve_path(current_path: str, target_path: str) -> str:
    """
    Resolve a target path relative to the current file path.

    Args:
        current_path: The path/URL of the current file.
        target_path: The target path/URL to resolve.

    Returns:
        The resolved absolute path/URL.
    """
    return PathResolver.resolve(current_path, target_path)


def _load_env_files(directories: list[Path]) -> None:
    """Load .env files from the specified directories."""
    for directory in directories:
        env_file = directory / ".env"
        if env_file.exists():
            load_dotenv(env_file)


# Register constructors for YamlLoader
_YamlLoader.add_constructor("tag:yaml.org,2002:str", _env_var_constructor)
_YamlLoader.add_constructor("!include", _include_file_constructor)
_YamlLoader.add_constructor("!include_raw", _include_raw_constructor)


def _load_yaml_from_string(
    content: str, original_uri: str | None = None
) -> dict[str, Any]:
    """
    Load a YAML file with environment variable substitution and file inclusion support.

    Args:
        content: The YAML content to load.
        original_uri: Optional URI of the original file for relative path resolution.

    Returns:
        The parsed YAML data with includes resolved and environment variables substituted.

    Raises:
        YAMLLoadError: If YAML parsing fails or environment variables are missing.
        FileNotFoundError: If the YAML file or included files don't exist.
    """

    # Create a string stream for the loader
    # Note: When loading from string, relative paths will be resolved relative to cwd
    stream = _StringStream(content, original_uri)

    try:
        # Use the string stream directly with the loader
        result = yaml.load(stream, Loader=_YamlLoader)
        return result  # type: ignore[no-any-return]
    except yaml.YAMLError as e:
        # Extract line/column information if available
        line = None
        column = None

        if hasattr(e, "problem_mark") and e.problem_mark:  # type: ignore[attr-defined]
            line = e.problem_mark.line  # type: ignore[attr-defined]
            column = e.problem_mark.column  # type: ignore[attr-defined]

        # Format a nice error message
        error_msg = str(e)
        if hasattr(e, "problem"):
            error_msg = e.problem or error_msg  # type: ignore[attr-defined]

        raise YAMLLoadError(
            message=f"YAML parsing error: {error_msg}",
            line=line,
            column=column,
            source=original_uri,
            original_error=e,
        ) from e
    except ValueError as e:
        # Environment variable substitution errors
        raise YAMLLoadError(
            message=str(e),
            source=original_uri,
            original_error=e,
        ) from e


def _load_yaml(content: str) -> dict[str, Any]:
    """
    Load a YAML file with environment variable substitution and file inclusion support.

    Args:
        content: Either a fsspec uri/file path to load, or a string containing YAML content.

    Returns:
        The parsed YAML data with includes resolved and environment variables substituted.

    Raises:
        YAMLLoadError: If YAML parsing fails or environment variables are missing.
        FileNotFoundError: If the YAML file or included files don't exist.
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
        return _load_yaml_from_string(content, original_uri)
    else:
        return _load_yaml_from_string(content)


def _resolve_root(doc: dsl.Document) -> dsl.DocumentType:
    """Extract the DocumentType from the Document wrapper.

    Simply returns doc.root which is one of the 9 DocumentType variants.
    """
    return doc.root


def _list_dynamic_types_from_document(
    loaded_yaml: dict[str, Any],
) -> list[dict]:
    """
    Build dynamic types from the loaded YAML data.

    Args:
        loaded_yaml: The parsed YAML data containing type definitions.

    Returns:
        A list of dynamic type definitions.
    """
    rv = []

    # add any "types" if the loaded doc is an application
    if isinstance(loaded_yaml, dict):
        rv.extend(loaded_yaml.get("types", []))

    # check for TypeList by seeing if we have root + custom types
    if "root" in loaded_yaml:
        root = loaded_yaml["root"]
        if (
            isinstance(root, list)
            and len(root) > 0
            and "properties" in root[0]
        ):
            rv.extend(root)

    # call recursively for any references
    if "references" in loaded_yaml:
        for ref in loaded_yaml["references"]:
            rv.extend(_list_dynamic_types_from_document(ref))
    return rv


def _simplify_field_path(loc: tuple) -> str:
    """
    Simplify a Pydantic error location path to be more readable.

    Removes verbose union type names and array indices, keeping only
    the essential field names.

    Args:
        loc: The error location tuple from Pydantic

    Returns:
        A simplified, readable field path string
    """
    simplified = []
    for part in loc:
        part_str = str(part)

        # Skip union type discriminator paths (they're too verbose)
        if "tagged-union" in part_str or "Union[" in part_str:
            continue

        # Skip Reference wrapper types
        if part_str.startswith("Reference["):
            continue

        # Keep numeric indices but format them as array indices
        if isinstance(part, int):
            simplified.append(f"[{part}]")
        else:
            simplified.append(part_str)

    return " -> ".join(simplified).replace(" -> [", "[")


def _is_relevant_error(error: dict) -> bool:
    """
    Determine if a validation error is relevant to show to the user.

    Filters out noise like:
    - "Input should be a valid list" for document type selection
    - Duplicate Reference resolution errors

    But keeps actual field validation errors even if they're inside unions.

    Args:
        error: A Pydantic error dictionary

    Returns:
        True if the error should be shown to the user
    """
    loc_str = " -> ".join(str(loc) for loc in error["loc"])
    error_type = error["type"]

    # Filter out "should be a valid list" errors for document types
    # These are just saying "this isn't a ModelList/ToolList/etc"
    if error_type == "list_type" and any(
        doc_type in loc_str
        for doc_type in [
            "AuthorizationProviderList",
            "ModelList",
            "ToolList",
            "TypeList",
            "VariableList",
            "AgentList",
            "FlowList",
            "IndexList",
        ]
    ):
        return False

    # Filter out Reference wrapper errors that are about $ref field
    # These are duplicates of the actual validation error
    if "Reference[" in loc_str and "$ref" in error["loc"][-1]:
        return False

    return True


def _format_validation_errors(
    validation_error: Any, source_name: str | None
) -> str:
    """
    Format Pydantic validation errors in a user-friendly way.

    Args:
        validation_error: The ValidationError from Pydantic
        source_name: Optional source file name for context

    Returns:
        A formatted error message string
    """
    # Filter and collect relevant errors
    relevant_errors = [
        error
        for error in validation_error.errors()
        if _is_relevant_error(error)
    ]

    if not relevant_errors:
        # Fallback if all errors were filtered
        error_msg = "Validation failed (see details above)"
    else:
        error_msg = "Validation failed:\n"
        for error in relevant_errors:
            loc_path = _simplify_field_path(error["loc"])
            error_msg += f"  {loc_path}: {error['msg']}\n"

    if source_name:
        error_msg = f"In {source_name}:\n{error_msg}"

    return error_msg


def load_document(content: str) -> tuple[dsl.DocumentType, CustomTypeRegistry]:
    """
    Load a QType YAML file and return the DSL document.

    Args:
        content: Either a fsspec uri/file path to load, or a string containing YAML content.

    Returns:
        A tuple of (DocumentType, CustomTypeRegistry) where DocumentType is one of:
        Agent, Application, AuthorizationProviderList, Flow, IndexList, ModelList,
        ToolList, TypeList, or VariableList.

    Raises:
        YAMLLoadError: If YAML parsing fails.
        ValueError: If Pydantic validation fails.
        FileNotFoundError: If the YAML file or included files don't exist.
    """
    from pydantic import ValidationError

    # Determine source name for error messages
    source_name = None
    if "\n" not in content:
        try:
            parsed = urlparse(content)
            if parsed.scheme in ["file", ""]:
                source_name = content
            elif parsed.scheme:
                source_name = content
        except Exception:
            pass

    try:
        yaml_data = _load_yaml(content)
        dynamic_types_lists = _list_dynamic_types_from_document(yaml_data)
        dynamic_types_registry = build_dynamic_types(dynamic_types_lists)
        document = dsl.Document.model_validate(
            yaml_data, context={"custom_types": dynamic_types_registry}
        )
        root = _resolve_root(document)
        return root, dynamic_types_registry
    except ValidationError as e:
        # Enhance Pydantic validation errors with context
        error_msg = _format_validation_errors(e, source_name)
        raise ValueError(error_msg) from e
