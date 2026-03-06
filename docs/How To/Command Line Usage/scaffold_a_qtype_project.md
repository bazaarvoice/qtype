# Scaffold A QType Project

Bootstrap a new QType application with a production-ready project structure using the official cookiecutter template, which generates a working AI application, tool definitions, Docker support, and VS Code integration.

## Prerequisites

- [cookiecutter](https://cookiecutter.readthedocs.io/en/latest/installation.html) installed (`pip install cookiecutter`)
- [uv](https://docs.astral.sh/uv/getting-started/installation/) installed for dependency management

## Run the Template

```bash
cookiecutter gh:bazaarvoice/qtype --directory template
```

You will be prompted for a single value:

```
project_name [My Project]: My Project
```

- **`project_name`**: Human-readable name for your project (e.g., `Customer Support Bot`)
- **Slug** (e.g., `customer-support-bot`): Auto-derived — used as directory name and YAML file prefix
- **Module name** (e.g., `customer_support_bot`): Auto-derived — used as the Python package name

## Generated Project Structure

```
my-project/
├── my_project/                          # Python tools package
│   ├── __init__.py
│   └── tools.py                         # Custom tool functions (greet, analyze_text)
├── my-project.qtype.yaml                # Main QType application
├── my-project.tools.qtype.yaml          # Generated tool definitions
├── pyproject.toml                       # Project metadata with qtype[interpreter,mcp] dependency
├── Dockerfile                           # Container image definition
└── .vscode/
    ├── launch.json                      # VS Code debug configurations
    └── mcp.json                         # MCP server config for Claude integration
```

### Explanation

- **`my_project/tools.py`**: Python module containing custom tool functions invokable from QType steps via `InvokeTool`
- **`my-project.qtype.yaml`**: Main application YAML — defines auth, model, and a sample `ask` flow wired to your tools and an LLM
- **`my-project.tools.qtype.yaml`**: Auto-generated tool declarations imported by the main YAML via `references`
- **`pyproject.toml`**: Declares `qtype[interpreter,mcp]` as a dependency; managed by `uv`
- **`Dockerfile`**: Packages the app into a container that runs `qtype serve`
- **`.vscode/mcp.json`**: Registers the project as an MCP server so Claude Desktop can invoke your flows

## Post-Scaffold Setup

```bash
# 1. Enter the project directory
cd my-project

# 2. Install dependencies
uv sync

# 3. Create a .env file with your API key
echo "OPENAI_API_KEY=sk-..." > .env

# 4. Validate the application spec
qtype validate my-project.qtype.yaml

# 5. Serve with hot-reload during development
qtype serve --reload my-project.qtype.yaml

# 6. Or run a flow directly from the CLI
qtype run my-project.qtype.yaml --flow ask \
  --input '{"user_name": "Alice", "user_question": "What is ML?"}'
```

## Regenerating Tool Definitions

After editing `my_project/tools.py`, regenerate the tool declarations:

```bash
qtype convert module my_project.tools -o my-project.tools.qtype.yaml
```

## Docker

```bash
docker build -t my-project .
docker run -p 8000:8000 --env-file .env my-project
```

## See Also

- [Serve With Auto Reload](serve_with_auto_reload.md)
- [Pass Inputs On The CLI](pass_inputs_on_the_cli.md)
- [Create Tools from Python Modules](../Tools%20&%20Integration/create_tools_from_python_modules.md)
- [Bind Tool Inputs and Outputs](../Tools%20&%20Integration/bind_tool_inputs_and_outputs.md)
