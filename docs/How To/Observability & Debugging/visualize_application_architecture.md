# Visualize Application Architecture

Generate interactive diagrams showing your application's flows, steps, and data dependencies to understand structure and debug issues.

## Example Visualization

Here's what a visualization looks like for a conversational chatbot application:

```mermaid
--8<-- "How To/Observability & Debugging/visualize_example.mermaid"
```

This diagram shows:

- **Flow structure**: The conversational flow with its interface and steps
- **Data flow**: How variables (user_message, context, response) flow between steps
- **Shared resources**: The LLM model and memory used by the application
- **Step types**: Different icons for templates (📄), LLM inference (✨), and other components

## Command Line

```bash
# Generate and open diagram in browser
qtype visualize path/to/app.qtype.yaml

# Save Mermaid diagram to file
qtype visualize path/to/app.qtype.yaml --output diagram.mmd

# Save without opening browser
qtype visualize path/to/app.qtype.yaml --output diagram.mmd --no-display
```

## Prerequisites

Visualization requires [mermaid-cli](https://github.com/mermaid-js/mermaid-cli) to be installed:

```bash
npm install -g @mermaid-js/mermaid-cli
```

## How It Works

- **Generates Mermaid diagram**: Creates a flowchart showing flows, steps, and variable connections
- **Converts to SVG**: Uses `mmdc` to render the diagram as a scalable vector graphic
- **Opens in browser**: Displays the interactive diagram automatically (unless `--no-display` is set)

## Options

- **`--output` / `-o`**: Save the Mermaid diagram source to a file (`.mmd` format)
- **`--no-display` / `-nd`**: Skip opening the diagram in browser (useful for CI/CD)

## Exit Codes

- **0**: Visualization successful
- **1**: Visualization failed (invalid YAML or missing mmdc)

## See Also

- [Validate QType YAML](validate_qtype_yaml.md)
- [Application Reference](../../components/Application.md)
- [Flow Reference](../../components/Flow.md)
