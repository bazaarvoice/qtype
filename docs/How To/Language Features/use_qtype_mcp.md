# Use QType MCP

QType's Model Context Protocol (MCP) server enables AI assistants like GitHub Copilot to lookup schemas and documentation, validate and visualize qtype files, and convert python modules or apis to tools directly from your AI workflow.

## Command Line Usage

Start the MCP server manually for debugging or other tools:

```bash
# Stdio transport (for VS Code, Claude Desktop, etc.)
qtype mcp --transport stdio

# HTTP/SSE transport (for web-based tools)
qtype mcp --transport sse --host 0.0.0.0 --port 8000
```

### Transport Options

- **stdio**: Standard input/output (default, for desktop tools)
- **sse**: Server-Sent Events over HTTP
- **streamable-http**: HTTP streaming protocol

## Available MCP Tools

The QType MCP server provides these capabilities to AI assistants:

- **convert_api_to_tools**: Convert OpenAPI specs to QType tool definitions
- **convert_python_to_tools**: Convert Python modules to QType tools
- **get_component_schema**: Retrieve JSON Schema for any QType component
- **get_documentation**: Fetch specific documentation files
- **list_components**: List all available QType component types
- **list_documentation**: Browse available documentation
- **validate_qtype_yaml**: Validate QType YAML syntax and semantics
- **visualize_qtype_architecture**: Generate Mermaid diagrams from QType apps


## VS Code Configuration

Add the QType MCP server to your workspace's `.vscode/mcp.json`:

```json
{
  "servers": {
    "qtype": {
      "type": "stdio",
      "command": "qtype",
      "cwd": "${workspaceFolder}",
      "args": ["mcp", "--transport", "stdio"]
    }
  }
}
```


## See Also

- [MCP Server Implementation](../../components/MCP.md)
- [GitHub Copilot Documentation](https://code.visualstudio.com/docs/copilot/copilot-chat)
- [Model Context Protocol](https://modelcontextprotocol.io/)
