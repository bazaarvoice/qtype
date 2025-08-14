# Installation

QType can be installed in two different ways depending on your needs:

## Interpreter Package Installation (Recommended)

For full functionality including the ability to execute QType flows, serve them as APIs, and launch user experiences, install with the interpreter extra:

=== "uv"
    ```sh
    uv add qtype[interpreter]
    ```

=== "pip"
    ```bash
    pip install qtype[interpreter]
    ```


## Base Package Installation

The base QType package provides core functionality for defining, validating, and generating schemas for QType specifications:

=== "uv"
    ```sh
    uv add qtype
    ```

=== "uvx"
    ```sh
    uvx qtype
    ```

=== "pip"
    ```sh
    pip install qtype
    ```

### What's included in the base package:

- **Schema validation**: Validate your QType YAML files against the specification
- **Schema generation**: Generate JSON schemas for your QType specifications  
- **File conversion**: Convert between different QType formats
- **Core DSL components**: Define models, prompts, tools, and flows
- **Basic CLI commands**: `validate`, `generate`, `convert`


### Additional capabilities with the interpreter package:

- **Flow execution**: Run QType flows locally with the `run` command
- **UI and API serving**: Serve QType flows as web UI and APIs with the `serve` command
- **Multiple model Providers**: Support for AWS Bedrock, OpenAI, and other LLM providers
- **Embeddings and Detrieval**: Built-in support for vector embeddings and retrieval
- **Observability**: Integrated telemetry and tracing with OpenTelemetry

### Additional dependencies:
- `boto3` - AWS SDK for Bedrock and other AWS services
- `fastapi` - Web framework for serving APIs
- `uvicorn` - ASGI server for FastAPI
- `llama-index` - LLM application framework with embeddings support
- `arize-phoenix-otel` - OpenTelemetry instrumentation

## Requirements

- **Python 3.10 or higher**
- Operating systems: macOS, Linux, Windows

## Verification

After installation, verify that QType is working correctly:

```bash
# Check installation
qtype --help

# Validate a sample spec (base package)
qtype validate examples/hello_world.qtype.yaml

# Run a flow (interpreter package only)
qtype run flow '{"user_message":"Hello, world!"}' examples/hello_world.qtype.yaml
```

