from __future__ import annotations

import json
import re
import tempfile
from functools import lru_cache
from importlib.resources import files
from pathlib import Path
from typing import Any

import tantivy
from mcp.server.fastmcp import FastMCP
from pydantic import BaseModel

from qtype.commands.convert import convert_to_yaml

# Initialize FastMCP server
mcp = FastMCP("qtype", host="0.0.0.0")

# Regex for pymdownx snippets: --8<-- "path/to/file"
SNIPPET_REGEX = re.compile(r'--8<--\s+"([^"]+)"')


# ============================================================================
# Resource Abstraction Layer
# ============================================================================


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
        except ValueError:
            raise ValueError(
                f"Invalid path: '{file_path}' is outside {self.name} directory"
            )

        if not requested_file.exists():
            raise FileNotFoundError(
                f"{self.name.capitalize()} file not found: '{file_path}'. "
                f"Use list_{self.name} to see available files."
            )

        if not requested_file.is_file():
            raise ValueError(f"Path is not a file: '{file_path}'")

        content = requested_file.read_text(encoding="utf-8")

        # Apply snippet resolution if enabled
        if self.resolve_snippets:
            content = _resolve_snippets(content, requested_file)

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
                f"{self.name.capitalize()} directory not found: {resource_path}"
            )

        # Find all files with the configured extension
        pattern = f"*{self.file_extension}"
        files_list = []
        for file in resource_path.rglob(pattern):
            # Get relative path from resource root
            rel_path = file.relative_to(resource_path)
            files_list.append(str(rel_path))

        return sorted(files_list)


# Initialize resource directories
_docs_resource = ResourceDirectory("docs", ".md", resolve_snippets=True)
_examples_resource = ResourceDirectory("examples", ".yaml")


# ============================================================================
# Helper Functions
# ============================================================================


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
        schema_file = files("qtype") / "schema" / "qtype.schema.json"
        schema_text = schema_file.read_text(encoding="utf-8")
        return json.loads(schema_text)
    except (FileNotFoundError, AttributeError):
        # Fall back to development path
        schema_path = (
            Path(__file__).parent.parent.parent / "schema/qtype.schema.json"
        )
        with open(schema_path, encoding="utf-8") as f:
            return json.load(f)


def _resolve_snippets(content: str, base_path: Path) -> str:
    """
    Recursively finds and replaces MkDocs snippets in markdown content.
    Mimics the behavior of pymdownx.snippets.

    Args:
        content: The markdown content to process
        base_path: Path to the file being processed (used to resolve relative paths)
    """
    docs_root = _docs_resource.get_path()
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
                return _resolve_snippets(
                    candidate.read_text(encoding="utf-8"), candidate
                )

        return f"> [!WARNING] Could not resolve snippet: {snippet_path}"

    return SNIPPET_REGEX.sub(replace_match, content)


@lru_cache(maxsize=1)
def _build_search_index() -> tantivy.Index:
    """Build and cache a Tantivy search index for docs and examples.

    Returns:
        A Tantivy Index containing all documentation markdown files
        and example YAML files.

    Raises:
        Exception: If index building fails.
    """
    docs_path = _docs_resource.get_path()
    examples_path = _examples_resource.get_path()

    # Create schema with fields for title, path, and content
    schema_builder = tantivy.SchemaBuilder()
    schema_builder.add_text_field("title", stored=True)
    schema_builder.add_text_field("path", stored=True)
    schema_builder.add_text_field("content", stored=True)
    schema_builder.add_text_field("type", stored=True)
    schema = schema_builder.build()

    # Create index in temporary directory
    index = tantivy.Index(schema, path=tempfile.mkdtemp())
    writer = index.writer()

    # Helper to index files
    def index_files(
        root_path: Path,
        pattern: str,
        type_label: str,
        path_prefix: str,
        process_content=None,
        extract_title=None,
    ):
        for file_path in root_path.rglob(pattern):
            content = file_path.read_text(encoding="utf-8")
            if process_content:
                content = process_content(content, file_path)

            rel_path = str(file_path.relative_to(root_path))
            title = (
                extract_title(content, file_path)
                if extract_title
                else file_path.stem
            )

            writer.add_document(
                tantivy.Document(
                    title=title,
                    path=f"{path_prefix}/{rel_path}",
                    content=content,
                    type=type_label,
                )
            )

    # Extract title from markdown first heading
    def extract_md_title(content: str, file_path: Path) -> str:
        for line in content.split("\n"):
            if line.startswith("# "):
                return line[2:].strip()
        return file_path.stem

    # Index documentation and examples
    index_files(
        docs_path,
        "*.md",
        "documentation",
        "docs",
        process_content=_resolve_snippets,
        extract_title=extract_md_title,
    )
    index_files(examples_path, "*.yaml", "example", "examples")

    writer.commit()
    return index


# ============================================================================
# Tool Functions
# ============================================================================


class MermaidDiagramPreviewInput(BaseModel):
    """Arguments for VS Code's `mermaid-diagram-preview` tool."""

    code: str


class MermaidVisualizationResult(BaseModel):
    """Structured output for Mermaid visualization."""

    mermaid_code: str
    mermaid_markdown: str
    suggested_next_tool: str
    mermaid_diagram_preview_input: MermaidDiagramPreviewInput
    preview_instructions: str


# Rebuild model after nested dependency is defined
MermaidVisualizationResult.model_rebuild()


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
        The full markdown content of the documentation file with snippets resolved.

    Raises:
        FileNotFoundError: If the specified file doesn't exist.
        ValueError: If the path tries to access files outside the docs directory.
    """
    return _docs_resource.get_file(file_path)


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
    return _docs_resource.list_files()


@mcp.tool(
    title="Get QType Example",
    description=(
        "Returns the content of a specific example YAML file. "
        "Use list_examples first to see available files. "
        "Provide the relative path (e.g., 'conversational_ai/simple_chatbot.qtype.yaml', "
        "'data_processing/csv_processor.qtype.yaml')."
    ),
)
def get_example(file_path: str) -> str:
    """Get the content of a specific example file.

    Args:
        file_path: Relative path to the example file from the examples root.
            Example: "conversational_ai/simple_chatbot.qtype.yaml",
            "data_processing/csv_processor.qtype.yaml".
            Use list_examples to see all available files.

    Returns:
        The full YAML content of the example file.

    Raises:
        FileNotFoundError: If the specified file doesn't exist.
        ValueError: If the path tries to access files outside the examples directory.
    """
    return _examples_resource.get_file(file_path)


@mcp.tool(
    title="List QType Examples",
    description=(
        "Returns a list of all available example YAML files. "
        "Use this to discover what examples exist, then retrieve "
        "specific files with get_example. Examples are organized by category: "
        "conversational_ai/ (chatbots and agents), data_processing/ (ETL and transformations), "
        "invoke_models/ (LLM usage), language_features/ (QType syntax examples), etc."
    ),
    structured_output=True,
)
def list_examples() -> list[str]:
    """List all available example YAML files.

    Returns:
        Sorted list of relative paths to all .yaml example files.
        Paths are relative to the examples root (e.g.,
        "conversational_ai/simple_chatbot.qtype.yaml",
        "data_processing/csv_processor.qtype.yaml").
    """
    return _examples_resource.list_files()


@mcp.tool(
    title="Search QType Library",
    description=(
        "Full-text search across all QType documentation and examples. "
        "Returns matching documents and example YAML files ranked by relevance. "
        "Use this to find documentation about specific topics, features, or components, "
        "or to discover example implementations. Doc paths can be used with get_documentation."
    ),
    structured_output=True,
)
def search_library(query: str, limit: int = 10) -> list[dict[str, Any]]:
    """Search library using full-text search.

    Args:
        query: Search query string. Can include multiple words, phrases,
            or boolean operators (AND, OR, NOT).
        limit: Maximum number of results to return (default: 10, max: 50).

    Returns:
        List of matching items with:
        - title: Item title
        - path: Relative path (docs/ or examples/ prefix)
        - type: Either "documentation" or "example"
        - score: Relevance score (higher is more relevant)

    Examples:
        search_library("flow execution")  # Find docs/examples about flows
        search_library("DocumentSource")  # Find component docs
        search_library("authentication AND API")  # Boolean search
    """
    # Clamp limit to reasonable range
    limit = max(1, min(limit, 50))

    index = _build_search_index()
    index.reload()
    searcher = index.searcher()
    tantivy_query = index.parse_query(query, ["title", "content"])

    search_results = searcher.search(tantivy_query, limit)

    results = []
    for score, doc_address in search_results.hits:
        doc = searcher.doc(doc_address)
        results.append(
            {
                "title": doc["title"][0],
                "path": doc["path"][0],
                "type": doc["type"][0],
                "score": score,
            }
        )

    return results


@mcp.tool(
    title="Validate QType YAML",
    description=(
        "Validates QType YAML for syntax and semantic correctness. "
        "Returns a human-readable status string: either a success message or "
        "a validation error with details."
    ),
)
async def validate_qtype_yaml(yaml_content: str) -> str:
    """Validate QType YAML for syntax and semantic errors.

    Args:
        yaml_content: The QType YAML content to validate.

    Returns:
        A human-readable status string.
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
        "Returns a structured result containing raw Mermaid code plus preview guidance. "
        "After calling this tool, call the mermaid-diagram-preview tool using the "
        "returned mermaid_diagram_preview_input."
    ),
    structured_output=True,
)
async def visualize_qtype_architecture(
    yaml_content: str,
) -> MermaidVisualizationResult:
    """Generate Mermaid diagram from QType YAML.

    Args:
        yaml_content: The complete QType YAML specification to visualize.
            Must be a valid Application definition.

    Returns:
        A structured result with:
        - mermaid_code: Raw Mermaid diagram code (no backticks/fences)
        - suggested_next_tool: "mermaid-diagram-preview"
        - preview_instructions: How to preview in VS Code

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

        return MermaidVisualizationResult(
            mermaid_code=mermaid_content,
            mermaid_markdown=f"```mermaid\n{mermaid_content}\n```\n",
            suggested_next_tool="mermaid-diagram-preview",
            mermaid_diagram_preview_input=MermaidDiagramPreviewInput(
                code=mermaid_content
            ),
            preview_instructions=(
                "Call mermaid-diagram-preview with mermaid_diagram_preview_input. "
                "Alternatively, save mermaid_code in a .md file fenced with "
                "```mermaid ...``` and open the Markdown preview."
            ),
        )

    except Exception as e:
        raise RuntimeError(f"Visualization failed: {e}") from e
