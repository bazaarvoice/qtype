"""Resource directory access utilities for QType package resources."""

from __future__ import annotations

import re
from functools import lru_cache
from importlib.resources import files
from pathlib import Path

# Regex for pymdownx snippets: --8<-- "path/to/file"
SNIPPET_REGEX = re.compile(r'--8<--\s+"([^"]+)"')


class ResourceDirectory:
    """Abstraction for accessing resource directories (docs, examples, etc.)."""

    def __init__(
        self, name: str, file_extension: str, resolve_snippets: bool = False
    ):
        """Initialize a resource directory.

        Args:
            name: Directory name (e.g., "docs", "examples")
            file_extension: File extension to search for (e.g., ".md", ".yaml")
            resolve_snippets: Whether to resolve MkDocs snippets in file content
        """
        self.name = name
        self.file_extension = file_extension
        self.resolve_snippets = resolve_snippets
        self._path_cache: Path | None = None

    def get_path(self) -> Path:
        """Get the path to this resource directory.

        Returns:
            Path to the resource directory, trying installed package first,
            then falling back to development path.
        """
        if self._path_cache is not None:
            return self._path_cache

        try:
            # Try to get from installed package
            resource_root = files("qtype") / self.name
            # Check if it exists by trying to iterate
            list(resource_root.iterdir())
            self._path_cache = Path(str(resource_root))
        except (FileNotFoundError, AttributeError, TypeError):
            # Fall back to development path
            self._path_cache = Path(__file__).parent.parent.parent / self.name

        return self._path_cache

    def get_file(self, file_path: str) -> str:
        """Get the content of a specific file.

        Args:
            file_path: Relative path to the file from the resource root.

        Returns:
            The full content of the file.

        Raises:
            FileNotFoundError: If the specified file doesn't exist.
            ValueError: If the path tries to access files outside the directory.
        """
        resource_path = self.get_path()

        # Resolve the requested file path
        requested_file = (resource_path / file_path).resolve()

        # Security check: ensure the resolved path is within resource directory
        try:
            requested_file.relative_to(resource_path.resolve())
        except ValueError as e:
            raise ValueError(
                f"Invalid path: '{file_path}' is outside {self.name} directory"
            ) from e

        if not requested_file.exists():
            raise FileNotFoundError(
                (
                    f"{self.name.capitalize()} file not found: '{file_path}'. "
                    f"Use list_{self.name} to see available files."
                )
            )

        if not requested_file.is_file():
            raise ValueError(f"Path is not a file: '{file_path}'")

        content = requested_file.read_text(encoding="utf-8")

        # Apply snippet resolution if enabled
        if self.resolve_snippets:
            content = _resolve_snippets(content, requested_file, self)

        return content

    def list_files(self) -> list[str]:
        """List all files in this resource directory.

        Returns:
            Sorted list of relative paths to all files with the configured extension.

        Raises:
            FileNotFoundError: If the resource directory doesn't exist.
        """
        resource_path = self.get_path()

        if not resource_path.exists():
            raise FileNotFoundError(
                (
                    f"{self.name.capitalize()} directory not found: "
                    f"{resource_path}"
                )
            )

        # Find all files with the configured extension
        pattern = f"*{self.file_extension}"
        files_list = []
        for file in resource_path.rglob(pattern):
            # Get relative path from resource root
            rel_path = file.relative_to(resource_path)
            files_list.append(str(rel_path))

        return sorted(files_list)


def _resolve_snippets(
    content: str, base_path: Path, docs_resource: ResourceDirectory
) -> str:
    """Recursively resolve MkDocs snippets in markdown content.

    Mimics the behavior of pymdownx.snippets.

    Args:
        content: The markdown content to process
        base_path: Path to the file being processed (for resolving relative paths)
        docs_resource: The docs ResourceDirectory for resolving snippet paths

    Returns:
        Content with all snippets resolved
    """
    docs_root = docs_resource.get_path()
    project_root = docs_root.parent

    def replace_match(match: re.Match) -> str:
        snippet_path = match.group(1)

        # pymdownx logic: try relative to current file, then docs, then project
        candidates = [
            base_path.parent / snippet_path,  # Relative to the doc file
            docs_root / snippet_path,  # Relative to docs root
            project_root / snippet_path,  # Relative to project root
        ]

        for candidate in candidates:
            if candidate.exists() and candidate.is_file():
                # Recursively resolve snippets inside the included file
                return _resolve_snippets(
                    candidate.read_text(encoding="utf-8"),
                    candidate,
                    docs_resource,
                )

        return f"> [!WARNING] Could not resolve snippet: {snippet_path}"

    return SNIPPET_REGEX.sub(replace_match, content)


# Initialize singleton resource directories
_docs_resource = ResourceDirectory("docs", ".md", resolve_snippets=True)
_examples_resource = ResourceDirectory("examples", ".yaml")


@lru_cache(maxsize=1)
def get_docs_resource() -> ResourceDirectory:
    """Get the singleton docs resource directory.

    Returns:
        ResourceDirectory instance for documentation files.
    """
    return _docs_resource


@lru_cache(maxsize=1)
def get_examples_resource() -> ResourceDirectory:
    """Get the singleton examples resource directory.

    Returns:
        ResourceDirectory instance for example files.
    """
    return _examples_resource
