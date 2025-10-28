"""
Simple YAML loading with environment variable and file inclusion support.

This module provides a clean, straightforward interface for loading YAML files
with support for:
- Environment variable substitution (${VAR} or ${VAR:default})
- File inclusion (!include and !include_raw)
- Multiple URI schemes via fsspec (local, http, s3, etc.)
"""

from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Any

import fsspec
import yaml
from dotenv import load_dotenv

from qtype.base.types import URILike
from qtype.dsl.parser import load_document  # noqa: F401


class YAMLLoadError(Exception):
    """Error during YAML loading or parsing."""

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
        """Format error message with location information."""
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


class YAMLLoader(yaml.SafeLoader):
    """YAML loader with env var substitution and file inclusion."""

    def __init__(self, stream: Any, base_path: str | None = None) -> None:
        super().__init__(stream)
        self.base_path = base_path or str(Path.cwd())


def _substitute_env_vars(value: str) -> str:
    """
    Substitute environment variables in a string.

    Supports ${VAR_NAME} or ${VAR_NAME:default} syntax.

    Args:
        value: String containing environment variable references

    Returns:
        String with environment variables substituted

    Raises:
        ValueError: If required environment variable is not found
    """
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


def _resolve_path(base_path: str, target_path: str) -> str:
    """
    Resolve a target path relative to base path.

    Uses fsspec's URL joining logic which handles both local paths and URIs.

    Args:
        base_path: Base path or URI
        target_path: Target path to resolve (relative or absolute)

    Returns:
        Resolved absolute path or URI
    """
    # If target is already absolute (has scheme or starts with /), use as-is
    from urllib.parse import urljoin, urlparse

    parsed = urlparse(target_path)
    if parsed.scheme or target_path.startswith("/"):
        return target_path

    # Check if base is URL-like
    base_parsed = urlparse(base_path)
    if base_parsed.scheme:
        # URL-based resolution
        return urljoin(base_path, target_path)
    else:
        # Local file resolution
        base_path_obj = Path(base_path)
        if not base_path_obj.is_dir():
            base_path_obj = base_path_obj.parent
        return str(base_path_obj / target_path)


def _env_var_constructor(loader: YAMLLoader, node: yaml.ScalarNode) -> str:
    """Constructor for environment variable substitution."""
    value = loader.construct_scalar(node)
    return _substitute_env_vars(value)


def _include_constructor(loader: YAMLLoader, node: yaml.ScalarNode) -> Any:
    """Constructor for !include tag to load external YAML files."""
    file_path = loader.construct_scalar(node)
    resolved_path = _resolve_path(loader.base_path, file_path)

    try:
        with fsspec.open(resolved_path, "r", encoding="utf-8") as f:
            content = f.read()  # type: ignore[misc]
            # Create a partial function to pass base_path to YAMLLoader
            from functools import partial

            loader_class = partial(YAMLLoader, base_path=resolved_path)
            return yaml.load(content, loader_class)  # type: ignore[arg-type]
    except Exception as e:
        raise FileNotFoundError(
            f"Failed to load included file '{resolved_path}': {e}"
        ) from e


def _include_raw_constructor(loader: YAMLLoader, node: yaml.ScalarNode) -> str:
    """Constructor for !include_raw tag to load external text files."""
    file_path = loader.construct_scalar(node)
    resolved_path = _resolve_path(loader.base_path, file_path)

    try:
        with fsspec.open(resolved_path, "r", encoding="utf-8") as f:
            return f.read()  # type: ignore[no-any-return]
    except Exception as e:
        raise FileNotFoundError(
            f"Failed to load included file '{resolved_path}': {e}"
        ) from e


# Register constructors
YAMLLoader.add_constructor("tag:yaml.org,2002:str", _env_var_constructor)
YAMLLoader.add_constructor("!include", _include_constructor)
YAMLLoader.add_constructor("!include_raw", _include_raw_constructor)


def load_yaml(source: URILike | str) -> dict[str, Any]:
    """
    Load YAML from file path/URI or string content.

    Args:
        source: URILike for file paths/URIs, or str for raw YAML content

    Returns:
        Parsed YAML as dictionary

    Raises:
        YAMLLoadError: If YAML parsing fails
        FileNotFoundError: If file doesn't exist
        ValueError: If required environment variable is missing
    """
    # Determine if source is a file/URI or raw YAML content
    if isinstance(source, URILike):
        # Load from file/URI
        source_str = source.path

        # Load .env file if it exists in the source directory
        try:
            from urllib.parse import urlparse

            parsed = urlparse(source_str)
            if parsed.scheme in ["file", ""]:
                # Local file - load .env from same directory
                source_path = Path(parsed.path if parsed.path else source_str)
                if source_path.is_file():
                    env_dir = source_path.parent
                    env_file = env_dir / ".env"
                    if env_file.exists():
                        load_dotenv(env_file)
        except Exception:
            pass

        # Also try cwd
        load_dotenv()

        # Load file content
        with fsspec.open(source_str, "r", encoding="utf-8") as f:
            content = f.read()  # type: ignore[misc]
        base_path = source_str
    else:
        # Load from string
        content = source
        base_path = str(Path.cwd())
        load_dotenv()

    # Parse YAML
    try:
        from functools import partial

        loader_class = partial(YAMLLoader, base_path=base_path)
        result = yaml.load(content, loader_class)  # type: ignore[arg-type]
        return result  # type: ignore[no-any-return]
    except yaml.YAMLError as e:
        # Extract line/column information if available
        line = None
        column = None

        if hasattr(e, "problem_mark") and e.problem_mark:  # type: ignore[attr-defined]
            line = e.problem_mark.line  # type: ignore[attr-defined]
            column = e.problem_mark.column  # type: ignore[attr-defined]

        # Format error message
        error_msg = str(e)
        if hasattr(e, "problem"):
            error_msg = e.problem or error_msg  # type: ignore[attr-defined]

        raise YAMLLoadError(
            message=f"YAML parsing error: {error_msg}",
            line=line,
            column=column,
            source=base_path if isinstance(source, URILike) else None,
            original_error=e,
        ) from e
    except ValueError as e:
        # Environment variable errors
        raise YAMLLoadError(
            message=str(e),
            source=base_path if isinstance(source, URILike) else None,
            original_error=e,
        ) from e
