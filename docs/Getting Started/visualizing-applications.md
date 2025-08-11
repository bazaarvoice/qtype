# Visualizing QType Applications

QType includes a  visualization feature that automatically generates Mermaid flowchart diagrams from your QType specifications. These visual diagrams help you understand the structure and flow of your AI applications at a glance.

## The `qtype visualize` Command

The `visualize` command analyzes your QType YAML specification and generates a comprehensive Mermaid diagram showing:

- **Flows** and their execution steps
- **Shared resources** like models, indexes, authentication, and memory
- **Connections** between components
- **Telemetry** and observability configuration

## Basic Usage

To generate a visualization of your QType application:

```bash
qtype visualize your_application.qtype.yaml
```

This will:
1. Load and validate your QType specification
2. Generate a Mermaid diagram
3. Open the diagram in your default browser for viewing

## Output Formats

The `visualize` command supports multiple output formats:

### Display in Browser (Default)
```bash
qtype visualize examples/chat_with_telemetry.qtype.yaml
```
Opens the diagram directly in your browser for immediate viewing.

### Save as Mermaid Source
```bash
qtype visualize examples/chat_with_telemetry.qtype.yaml -o diagram.mmd
```
Saves the raw Mermaid markup to a `.mmd` or `.mermaid` file.

### Export as SVG
```bash
qtype visualize examples/chat_with_telemetry.qtype.yaml -o diagram.svg
```
Generates a scalable vector graphics file perfect for documentation.

### Export as PNG
```bash
qtype visualize examples/chat_with_telemetry.qtype.yaml -o diagram.png
```
Creates a raster image file for presentations or embedding.

### Save Without Opening Browser
```bash
qtype visualize examples/chat_with_telemetry.qtype.yaml -o diagram.svg --no-display
```
Use the `--no-display` flag to save files without opening the browser.

## Example: Chat with Telemetry

Let's look at a practical example using the `chat_with_telemetry.qtype.yaml` file:

```yaml
id: hello_world
flows:
  - id: chat_example
    description: A simple chat flow with OpenAI
    mode: Chat
    steps:
      - id: llm_inference_step
        model: 
          id: gpt-4
          provider: openai
          auth: 
            id: openai_auth
            type: api_key
            api_key: ${OPENAI_KEY}
        system_message: |
          You are a helpful assistant.
        inputs:
          - id: user_message
            type: ChatMessage
        outputs:
          - id: response
            type: ChatMessage
telemetry:
  id: hello_world_telemetry
  endpoint: http://localhost:6006/v1/traces
```

Running the visualization command:

```bash
qtype visualize examples/chat_with_telemetry.qtype.yaml -o chat_with_telemetry.mermaid
```

Generates this Mermaid diagram:

```mermaid
--8<-- "Getting Started/chat_with_telemetry.mermaid"
```

## Understanding the Diagram

The generated diagram uses intuitive icons and colors to represent different components:

### Application Structure
- **📱 Application**: The outermost container showing your application ID
- **💬 Chat Flows** / **🔄 Flows**: Individual flows with their descriptions
- **✨ Steps**: Individual steps within flows (with different shapes for different step types)

### Shared Resources
- **🔐 Authentication**: API keys, OAuth, and other auth providers
- **✨ Models**: LLM models with their providers (OpenAI, Bedrock, etc.)
- **🗂️ Indexes**: Vector and document indexes for retrieval
- **🧠 Memory**: Conversation memory stores
- **🔧 Tools**: API tools, Python functions, and other capabilities

### Observability
- **📊 Telemetry**: OpenTelemetry tracing endpoints
- **📡 Telemetry Sink**: Where traces and metrics are sent

### Connections
- **Solid arrows** (`-->`) show data flow between steps
- **Dotted arrows** (`-.->`) show resource dependencies and relationships

## Command Reference

```
qtype visualize [OPTIONS] SPEC_FILE

Arguments:
  SPEC_FILE    Path to the QType YAML file to visualize

Options:
  -o, --output PATH     Save diagram to file (.mmd, .mermaid, .svg, .png)
  -nd, --no-display     Don't open diagram in browser (default: False)
  -h, --help           Show help message
```


## Tips for Better Visualizations

1. **Use descriptive IDs**: Clear, descriptive IDs for flows and steps make diagrams more readable
2. **Add descriptions**: Flow descriptions appear in the diagram and provide valuable context
3. **Group related functionality**: Organize steps logically within flows
4. **Keep flows focused**: Smaller, focused flows are easier to understand than large, complex ones

