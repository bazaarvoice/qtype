# Command Line Interface

The QType CLI lets you run applications, validate specifications, serve web interfaces, and generating resources.

## Installation

The QType CLI is installed with the qtype package. Run commands with:

```bash
qtype [command] [options]
```

## Global Options

```
--log-level {DEBUG,INFO,WARNING,ERROR,CRITICAL}
    Set the logging level (default: INFO)
```

## Commands

### run

Execute a QType application locally.

```bash
qtype run [options] spec
```

#### Arguments

- **`spec`** - Path to the QType YAML spec file

#### Options

- **`-f FLOW, --flow FLOW`** - The name of the flow to run. If not specified, runs the first flow found
- **`-i INPUT, --input INPUT`** - JSON blob of input values for the flow (default: `{}`)
- **`-I INPUT_FILE, --input-file INPUT_FILE`** - Path to a file (e.g., CSV, JSON, Parquet) with input data for batch processing
- **`-o OUTPUT, --output OUTPUT`** - Path to save output data. If input is a DataFrame, output will be saved as parquet. If single result, saved as JSON
- **`--progress`** - Show progress bars during flow execution

#### Examples

Run a simple application:
```bash
qtype run app.qtype.yaml
```

Run with inline JSON inputs:
```bash
qtype run app.qtype.yaml -i '{"question": "What is AI?"}'
```

Run a specific flow:
```bash
qtype run app.qtype.yaml --flow process_data
```

Batch process data from a file:
```bash
qtype run app.qtype.yaml --input-file inputs.csv --output results.parquet
```

#### See Also

- [How To: Pass Inputs On The CLI](../How%20To/Command%20Line%20Usage/pass_inputs_on_the_cli.md)
- [How To: Load Multiple Inputs from Files](../How%20To/Command%20Line%20Usage/load_multiple_inputs_from_files.md)
- [Tutorial: Your First QType Application](../Tutorials/01-first-qtype-application.md)

---

### validate

Validate a QType YAML spec against the schema and semantic rules.

```bash
qtype validate [options] spec
```

#### Arguments

- **`spec`** - Path to the QType YAML spec file

#### Options

- **`-p, --print`** - Print the spec after validation (default: False)

#### Examples

Validate a specification:
```bash
qtype validate app.qtype.yaml
```

Validate and print the parsed spec:
```bash
qtype validate app.qtype.yaml --print
```

#### See Also

- [How To: Validate QType YAML](../How%20To/Observability%20&%20Debugging/validate_qtype_yaml.md)
- [Reference: Semantic Validation Rules](semantic-validation-rules.md)

---

### serve

Serve a web experience for a QType application with an interactive UI.

```bash
qtype serve [options] spec
```

#### Arguments

- **`spec`** - Path to the QType YAML spec file

#### Options

- **`-p PORT, --port PORT`** - Port to run the server on (default: 8080)
- **`-H HOST, --host HOST`** - Host to bind the server to (default: 0.0.0.0)
- **`--reload`** - Enable auto-reload on code changes (default: False)

#### Examples

Serve an application:
```bash
qtype serve app.qtype.yaml
```

Serve on a specific port:
```bash
qtype serve app.qtype.yaml --port 3000
```

Serve with auto-reload for development:
```bash
qtype serve app.qtype.yaml --reload
```

#### See Also

- [How To: Serve Flows as APIs](../How%20To/Qtype%20Server/serve_flows_as_apis.md)
- [How To: Serve Flows as UI](../How%20To/Qtype%20Server/serve_flows_as_ui.md)
- [How To: Use Conversational Interfaces](../How%20To/Qtype%20Server/use_conversational_interfaces.md)
- [How To: Serve Applications with Auto-Reload](../How%20To/Qtype%20Server/serve_applications_with_auto_reload.md)
- [Tutorial: Building a Stateful Chatbot](../Tutorials/02-conversational-chatbot.md)

---

### visualize

Generate a visual diagram of your QType application architecture.

```bash
qtype visualize [options] spec
```

#### Arguments

- **`spec`** - Path to the QType YAML file

#### Options

- **`-o OUTPUT, --output OUTPUT`** - If provided, write the mermaid diagram to this file
- **`-nd, --no-display`** - If set, don't display the diagram in a browser (default: False)

#### Examples

Visualize and open in browser:
```bash
qtype visualize app.qtype.yaml
```

Save to file without displaying:
```bash
qtype visualize app.qtype.yaml --output diagram.mmd --no-display
```

Generate and save diagram:
```bash
qtype visualize app.qtype.yaml --output architecture.mmd
```

#### See Also

- [How To: Visualize Application Architecture](../How%20To/Observability%20&%20Debugging/visualize_application_architecture.md)

---

### convert

Create QType tool definitions from external sources.

```bash
qtype convert {module,api} [options]
```

#### Subcommands

##### convert module

Convert a Python module to QType tools format.

```bash
qtype convert module [options] module_path
```

**Arguments:**

- **`module_path`** - Path to the Python module to convert

**Options:**

- **`-o OUTPUT, --output OUTPUT`** - Output file path. If not specified, prints to stdout

**Examples:**

Convert a Python module:
```bash
qtype convert module myapp.utils --output tools.qtype.yaml
```

Print to stdout:
```bash
qtype convert module myapp.utils
```

**See Also:**

- [How To: Create Tools from Python Modules](../How%20To/Tools%20&%20Integration/create_tools_from_python_modules.md)
- [Tutorial: Adding Tools to Your Application](../Tutorials/04-tools-and-function-calling.md)

##### convert api

Convert an OpenAPI/Swagger specification to QType format.

```bash
qtype convert api [options] api_spec
```

**Arguments:**

- **`api_spec`** - Path to the API specification file (supports local files or URLs)

**Options:**

- **`-o OUTPUT, --output OUTPUT`** - Output file path. If not specified, prints to stdout

**Examples:**

Convert an OpenAPI spec:
```bash
qtype convert api spec.oas.yaml --output api_tools.qtype.yaml
```

Convert from a URL:
```bash
qtype convert api https://petstore3.swagger.io/api/v3/openapi.json --output petstore.qtype.yaml
```

**See Also:**

- [How To: Create Tools from OpenAPI Specifications](../How%20To/Tools%20&%20Integration/create_tools_from_openapi_specifications.md)
- [Tutorial: Adding Tools to Your Application](../Tutorials/04-tools-and-function-calling.md)

---

### generate

Generate QType project resources (primarily for internal development).

```bash
qtype generate {commons,schema,dsl-docs,semantic-model} [options]
```

This command is primarily used for QType development and maintenance.

#### Subcommands

- **`commons`** - Generates the commons library tools from `tools.py`
- **`schema`** - Generates the JSON schema for the QType DSL from `model.py`
- **`dsl-docs`** - Generates markdown documentation for the QType DSL classes from `model.py`
- **`semantic-model`** - Generates the semantic model from QType DSL (See [Contributing](../Contributing/))

---

## Exit Codes

- **0** - Success
- **1** - Error (validation failure, runtime error, etc.)

