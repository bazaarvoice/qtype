from __future__ import annotations

import json
import re
from functools import lru_cache
from importlib.resources import files
from pathlib import Path
from typing import Any

from mcp.server.fastmcp import FastMCP

from qtype.commands.convert import convert_to_yaml

# Initialize FastMCP server
mcp = FastMCP("qtype", host="0.0.0.0")

# Regex for pymdownx snippets: --8<-- "path/to/file"
SNIPPET_REGEX = re.compile(r'--8<--\s+"([^"]+)"')


# ============================================================================
# Helper Functions
# ============================================================================


def _get_docs_path() -> Path:
    """Get the path to the documentation directory.

    Returns:
        Path to the docs directory, trying installed package first,
        then falling back to development path.
    """
    try:
        # Try to get from installed package
        docs_root = files("qtype") / "docs"
        # Check if it exists by trying to iterate
        list(docs_root.iterdir())
        return Path(str(docs_root))
    except (FileNotFoundError, AttributeError, TypeError):
        # Fall back to development path
        return Path(__file__).parent.parent.parent / "docs"


@lru_cache(maxsize=1)
def _load_schema() -> dict[str, Any]:
    """Load the QType schema JSON file once and cache it.

    Returns:
        The complete schema as a dictionary.

    Raises:
        FileNotFoundError: If schema file doesn't exist.
        json.JSONDecodeError: If schema file is invalid JSON.
    """
    # Try to load from installed package data first
    try:
        schema_file = files("qtype") / "qtype.schema.json"
        schema_text = schema_file.read_text(encoding="utf-8")
        return json.loads(schema_text)
    except (FileNotFoundError, AttributeError):
        # Fall back to development path
        schema_path = (
            Path(__file__).parent.parent.parent / "schema/qtype.schema.json"
        )
        with open(schema_path, encoding="utf-8") as f:
            return json.load(f)


def resolve_snippets(content: str, base_path: Path) -> str:
    """
    Recursively finds and replaces MkDocs snippets in markdown content.
    Mimics the behavior of pymdownx.snippets.

    Args:
        content: The markdown content to process
        base_path: Path to the file being processed (used to resolve relative paths)
    """
    docs_root = _get_docs_path()
    project_root = docs_root.parent

    def replace_match(match):
        snippet_path = match.group(1)

        # pymdownx logic: try relative to current file, then relative to docs, then project root
        candidates = [
            base_path.parent / snippet_path,  # Relative to the doc file
            docs_root / snippet_path,  # Relative to docs root
            project_root / snippet_path,  # Relative to project root
        ]

        for candidate in candidates:
            if candidate.exists() and candidate.is_file():
                # Recursively resolve snippets inside the included file
                return resolve_snippets(
                    candidate.read_text(encoding="utf-8"), candidate
                )

        return f"> [!WARNING] Could not resolve snippet: {snippet_path}"

    return SNIPPET_REGEX.sub(replace_match, content)


# ============================================================================
# Tool Functions
# ============================================================================


@mcp.tool(
    title="Convert API Specification to QType Tools",
    description=(
        "Converts an OpenAPI specification (URL or file path) to QType tool definitions. "
        "Returns YAML code containing the generated tools, custom types, and authentication "
        "providers that can be used in QType applications."
    ),
)
async def convert_api_to_tools(api_spec: str) -> str:
    """Convert API specification to QType YAML format.

    Args:
        api_spec: URL or file path to an OpenAPI/Swagger specification.
            Examples: "https://api.example.com/openapi.json",
            "/path/to/openapi.yaml"

    Returns:
        YAML string containing the generated QType tools, types, and
        authentication providers.

    Raises:
        Exception: If conversion fails or no tools are found.
    """
    from qtype.application.converters.tools_from_api import tools_from_api
    from qtype.dsl.model import Application, ToolList

    try:
        api_name, auths, tools, types = tools_from_api(api_spec)
        if not tools:
            raise ValueError(
                f"No tools found from the API specification: {api_spec}"
            )

        # Create document with or without Application wrapper
        if not auths and not types:
            doc = ToolList(root=list(tools))
        else:
            doc = Application(
                id=api_name,
                description=(
                    f"Tools created from API specification {api_spec}"
                ),
                tools=list(tools),
                types=types,
                auths=auths,
            )

        return convert_to_yaml(doc)

    except Exception as e:
        raise Exception(f"API conversion failed: {str(e)}")


@mcp.tool(
    title="Convert Python Module to QType Tools",
    description=(
        "Converts Python functions from a module to QType tool definitions. "
        "Analyzes function signatures, docstrings, and type hints to generate "
        "YAML tool definitions that can be used in QType applications."
    ),
)
async def convert_python_to_tools(module_path: str) -> str:
    """Convert Python module to QType YAML format.

    Args:
        module_path: Path to the Python module to convert.
            Example: "my_package.my_module" or "/path/to/module.py"

    Returns:
        YAML string containing the generated QType tools and custom types.

    Raises:
        Exception: If conversion fails or no tools are found.
    """
    from qtype.application.converters.tools_from_module import (
        tools_from_module,
    )
    from qtype.dsl.model import Application, ToolList

    try:
        tools, types = tools_from_module(module_path)
        if not tools:
            raise ValueError(f"No tools found in the module: {module_path}")

        # Create document with or without Application wrapper
        if types:
            doc = Application(
                id=module_path,
                description=(
                    f"Tools created from Python module {module_path}"
                ),
                tools=list(tools),
                types=types,
            )
        else:
            doc = ToolList(root=list(tools))

        return convert_to_yaml(doc)

    except Exception as e:
        raise Exception(f"Python module conversion failed: {str(e)}")


@mcp.tool(
    title="Get QType Component Schema",
    description=(
        "Returns the JSON Schema definition for a specific QType component. "
        "Use this to understand the structure, required fields, and allowed values "
        "when building QType YAML specifications. "
        "Common components include: Flow, Agent, LLMInference, DocumentSource, "
        "Application, Model, Variable, CustomType. "
        "Component names are case-sensitive and must match exactly."
    ),
    structured_output=True,
)
def get_component_schema(component_name: str) -> dict[str, Any]:
    """Get the JSON Schema definition for a QType component.

    Args:
        component_name: The exact name of the QType component (case-sensitive).
            Examples: "DocumentSource", "Flow", "Agent", "LLMInference",
            "Application", "Model", "Variable", "CustomType".

    Returns:
        JSON Schema definition for the component including its properties,
        required fields, types, and descriptions.

    Raises:
        ValueError: If component_name is not found. The error message will
            include a list of all available component names.
    """
    schema = _load_schema()

    # Look up the component in $defs
    if "$defs" not in schema:
        raise ValueError("Schema file does not contain $defs section")

    if component_name not in schema["$defs"]:
        available = sorted(schema["$defs"].keys())
        raise ValueError(
            f"Component '{component_name}' not found in schema. "
            f"Available components: {', '.join(available)}"
        )

    return schema["$defs"][component_name]


@mcp.tool(
    title="Get QType Documentation",
    description=(
        "Returns the content of a specific documentation file. "
        "Use list_documentation first to see available files. "
        "Provide the relative path (e.g., 'components/Flow.md', 'index.md', "
        "'Tutorials/getting_started.md')."
    ),
)
def get_documentation(file_path: str) -> str:
    """Get the content of a specific documentation file.

    Args:
        file_path: Relative path to the documentation file from the docs root.
            Example: "components/Flow.md", "index.md", "Tutorials/getting_started.md".
            Use list_documentation to see all available files.

    Returns:
        The full markdown content of the documentation file.

    Raises:
        FileNotFoundError: If the specified file doesn't exist.
        ValueError: If the path tries to access files outside the docs directory.
    """
    docs_path = _get_docs_path()

    # Resolve the requested file path
    requested_file = (docs_path / file_path).resolve()

    # Security check: ensure the resolved path is within docs directory
    try:
        requested_file.relative_to(docs_path.resolve())
    except ValueError:
        raise ValueError(
            f"Invalid path: '{file_path}' is outside documentation directory"
        )

    if not requested_file.exists():
        raise FileNotFoundError(
            f"Documentation file not found: '{file_path}'. "
            "Use list_documentation to see available files."
        )

    if not requested_file.is_file():
        raise ValueError(f"Path is not a file: '{file_path}'")

    content = requested_file.read_text(encoding="utf-8")
    return resolve_snippets(content, requested_file)


@mcp.tool(
    title="List QType Components",
    description=(
        "Returns a list of all available QType component types that can be used "
        "in YAML specifications. Use this to discover what components exist before "
        "requesting their detailed schemas with get_component_schema."
    ),
    structured_output=True,
)
def list_components() -> list[str]:
    """List all available QType component types.

    Returns:
        Sorted list of all component names available in the QType schema.
        Each name can be used with get_component_schema to retrieve its
        full JSON Schema definition.
    """
    schema = _load_schema()

    if "$defs" not in schema:
        raise ValueError("Schema file does not contain $defs section")

    return sorted(schema["$defs"].keys())


@mcp.tool(
    title="List QType Documentation",
    description=(
        "Returns a list of all available documentation files. "
        "Use this to discover what documentation exists, then retrieve "
        "specific files with get_documentation. Files are organized by category: "
        "components/ (component reference), Concepts/ (conceptual guides), "
        "Tutorials/ (step-by-step tutorials), How To/ (task guides), etc."
    ),
    structured_output=True,
)
def list_documentation() -> list[str]:
    """List all available documentation markdown files.

    Returns:
        Sorted list of relative paths to all .md documentation files.
        Paths are relative to the docs root (e.g., "components/Flow.md",
        "Tutorials/getting_started.md").
    """
    docs_path = _get_docs_path()

    if not docs_path.exists():
        raise FileNotFoundError(
            f"Documentation directory not found: {docs_path}"
        )

    # Find all markdown files
    md_files = []
    for md_file in docs_path.rglob("*.md"):
        # Get relative path from docs root
        rel_path = md_file.relative_to(docs_path)
        md_files.append(str(rel_path))

    return sorted(md_files)


@mcp.tool()
async def validate_qtype_yaml(yaml_content: str) -> str:
    """
    Validates QType YAML code for syntax and semantic errors.
    Use this tool immediately after generating any QType code to verify correctness.
    """
    from qtype.semantic.loader import load_from_string

    try:
        document, _ = load_from_string(yaml_content)
        return "✅ Valid QType Code"

    except Exception as e:
        # Return the error message so the LLM can fix it
        return f"❌ Validation Error: {str(e)}"


@mcp.tool(
    title="Visualize QType Architecture",
    description=(
        "Generates a Mermaid flowchart diagram from QType YAML code. "
        "Returns the Mermaid diagram content along with instructions for preview. "
        "The diagram visualizes the application architecture, showing flows, "
        "components, and their connections."
    ),
)
async def visualize_qtype_architecture(yaml_content: str) -> str:
    """Generate Mermaid diagram from QType YAML.

    Args:
        yaml_content: The complete QType YAML specification to visualize.
            Must be a valid Application definition.

    Returns:
        A formatted response containing:
        1. Instructions on how to preview the diagram in VS Code
        2. The raw Mermaid diagram content
        3. Guidance on using the mermaid-diagram-preview tool

    Raises:
        Exception: If YAML is invalid or visualization fails.
    """
    from qtype.semantic.loader import load_from_string
    from qtype.semantic.model import Application
    from qtype.semantic.visualize import visualize_application

    try:
        document, _ = load_from_string(yaml_content)
        if not isinstance(document, Application):
            raise ValueError(
                "YAML must contain an Application to visualize. "
                f"Got {type(document).__name__} instead."
            )
        mermaid_content = visualize_application(document)

        # Return content with preview instructions
        return f"""✅ Diagram generated successfully!

To preview this diagram in VS Code:
1. Use the mermaid-diagram-preview tool with the code below
2. Or save it to a .md file with triple backticks: ```mermaid
3. Or save it to a .mmd file and use the Mermaid extension

Mermaid Diagram Code:
```mermaid
{mermaid_content}
```
"""

    except Exception as e:
        raise Exception(f"Visualization failed: {str(e)}")
