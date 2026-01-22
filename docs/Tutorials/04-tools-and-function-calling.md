# Adding Tools to Your Application

**Time:** 20 minutes  
**Prerequisites:** [Tutorial 3: Working with Types and Structured Data](03-structured-data.md)  
**Example:** [`04_tools_and_function_calling.qtype.yaml`](https://github.com/bazaarvoice/qtype/blob/main/examples/tutorials/04_tools_and_function_calling.qtype.yaml)

**What you'll learn:**

* Import pre-built tools from the commons library
* Use InvokeTool to call Python functions
* Chain multiple tools with input/output bindings
* Understand tool references and automatic generation

**What you'll build:** A deadline calculator that uses tools to get the current time, add days, and format the result.

---

## Background: What Are Tools?

Tools extend your QType applications with custom steps.
Tools are how you plug QType into other existing systems that may not be supported in the shipped interpreter.

**A tool is simply a reference to:**
- **A Python function** - Call any Python function with typed parameters
- **An API endpoint** - Make HTTP requests to external services

Tools define their **inputs** (parameters) and **outputs** (return values) with explicit types. 

### The Commons Library

QType provides a [commons library](https://github.com/bazaarvoice/qtype/blob/main/common/tools.qtype.yaml) published on GitHub with pre-built tools for common operations:

- **Time utilities** - Get current time, add/subtract durations, format timestamps
- **String operations** - Base64 encoding/decoding, text transformations
- **Data processing** - JSON parsing, field extraction, type conversions

### Automatic Tool Generation

You don't need to write tool YAML files manually! QType can generate them automatically using `qtype convert`:

**From Python modules:**
```bash
qtype convert python --module myapp.utils --output tools.qtype.yaml
```

**From OpenAPI specifications:**
```bash
qtype convert openapi --spec api_spec.yaml --output api_tools.qtype.yaml
```

The converter analyzes function signatures or API schemas and creates properly typed tool definitions. 

---

## Part 1: Import and Use Your First Tool (7 minutes)

### Create Your Application File

Create `04_tools_and_function_calling.qtype.yaml`:

```yaml
id: deadline_calculator
description: |
  Calculates a deadline by adding days to the current timestamp.
  Demonstrates tool imports, InvokeTool step, and tool chaining.
```

---

### Import the Commons Library

Add a `references:` section before `flows:`:

```yaml
# Import pre-built tools from the commons library
references:
  - !include ../../common/tools.qtype.yaml
```

**What this means:**

**`!include`** - YAML directive to load another file's content. `!include` brings in yaml files inside the header. 
- Can use local paths: `!include ../../common/tools.qtype.yaml`
- Or remote URLs: `!include https://...` (shown here)
- Imports all tools, types, and definitions from that file

**`references:` section** - Where you import external components. References can be other applications or lists of models, tools, authorization providers, variables, or custom types.

You can now reference any tool by its `id` (like `qtype.application.commons.tools.get_current_timestamp`).

**Check your work:**

```bash
qtype validate 04_tools_and_function_calling.qtype.yaml
```

Should pass ✅ (even with no flows yet - imports are valid)

---

### Define Your Flow Variables

Add the flow structure:

```yaml
flows:
  - id: calculate_deadline
    description: Calculate a formatted deadline from current time plus days
    inputs:
      - days_until_due
    outputs:
      - deadline_formatted

    variables:
      # Input
      - id: days_until_due
        type: int
      
      # Tool outputs
      - id: current_time
        type: datetime
      - id: deadline_time
        type: datetime
      - id: format_string
        type: text
      - id: deadline_formatted
        type: text
```

**New types:**

**`datetime` type** - Built-in QType type for timestamps:
- Represents a point in time (date + time)
- Stored internally as ISO 8601 strings
- Automatically converted to/from Python `datetime` objects
- Tools can accept and return `datetime` values

**Why all these variables?** Each tool transforms data:
- `current_time` ← output from get_current_timestamp
- `deadline_time` ← output from timedelta (current_time + days)
- `deadline_formatted` ← output from format_datetime (pretty string)

Explicit variables make the data flow visible and debuggable.

---

### Add Your First Tool Call

Add this under `steps:`:

```yaml
    steps:
      # Step 1: Get current timestamp using a tool
      # This tool takes no inputs and returns the current UTC time
      - id: get_current_time
        type: InvokeTool
        tool: qtype.application.commons.tools.get_current_timestamp
        input_bindings: {}
        output_bindings:
          result: current_time
        outputs:
          - current_time
```

**New step type: InvokeTool**

This is your primary way to call tools in QType flows.

**`tool:`** - Full ID of the tool to invoke:
- Format: `<module_id>.<function_name>` 
- Must match a tool defined in your imports or application
- Example: `qtype.application.commons.tools.get_current_timestamp`

**`input_bindings:`** - Maps flow variables to tool parameters:
- Empty `{}` means no inputs needed
- This tool has no parameters - it just returns the current time

**`output_bindings:`** - Maps tool outputs to flow variables:
- `result: current_time` means "take the tool's `result` output and store it in the `current_time` variable"
- Tool outputs are defined in the tool's YAML definition

**`outputs:`** - Flow-level outputs this step produces:
- Lists which flow variables this step creates or modifies
- Used by QType to validate data flow through the pipeline

**Check your work:**

```bash
qtype validate 04_tools_and_function_calling.qtype.yaml
```

Should pass ✅

---

## Part 2: Chain Tools with Bindings (8 minutes)

### Add a Constant Variable

Before we can format our datetime, we need to define the format string:

```yaml
      # Step 2: Create a format string constant
      - id: create_format_string
        type: PromptTemplate
        template: "%B %d, %Y at %I:%M %p UTC"
        inputs: []
        outputs:
          - format_string
```

**Pattern: Constants in flows**

Since tool `input_bindings` only accept variable names (not literal values), we use PromptTemplate to create constants:
- Template with no placeholders → constant string
- `inputs: []` → no dependencies
- Produces `format_string` variable for later use

**Format string syntax:** Uses Python's `strftime` format codes:
- `%B` - Full month name (January)
- `%d` - Day of month (14)
- `%Y` - 4-digit year (2026)
- `%I:%M %p` - Time in 12-hour format (03:30 PM)

---

### Add Days with Input Bindings

Now let's use a tool with multiple inputs:

```yaml
      # Step 3: Calculate deadline by adding days to current time
      # input_bindings maps flow variables to tool parameters
      - id: add_days
        type: InvokeTool
        tool: qtype.application.commons.tools.timedelta
        input_bindings:
          timestamp: current_time
          days: days_until_due
        output_bindings:
          result: deadline_time
        outputs:
          - deadline_time
```

**Understanding bindings:**

**Input bindings structure:**
```yaml
input_bindings:
  <tool_parameter_name>: <flow_variable_name>
```

In this case:
- Tool parameter `timestamp` ← gets value from flow variable `current_time`
- Tool parameter `days` ← gets value from flow variable `days_until_due`

The `timedelta` tool definition (from commons library) looks like:
```yaml
inputs:
  - id: timestamp
    type: datetime
  - id: days
    type: int?
  - id: hours
    type: int?
  # ... more optional parameters
```

**Optional parameters:** You only need to bind the required parameters. `timedelta` has many optional parameters (hours, minutes, seconds, weeks), but we only use `days`.

---

### Chain Tools Together

Finally, format the deadline using the output from the previous step:

```yaml
      # Step 4: Format deadline for human readability
      # Shows chaining: output from previous tool becomes input to this one
      - id: format_deadline
        type: InvokeTool
        tool: qtype.application.commons.tools.format_datetime
        input_bindings:
          timestamp: deadline_time
          format_string: format_string
        output_bindings:
          result: deadline_formatted
        outputs:
          - deadline_formatted
```

**Check your work:**

```bash
qtype validate 04_tools_and_function_calling.qtype.yaml
```

Should pass ✅

---

## Part 3: Test Your Tools (5 minutes)

### Run the Application

```bash
qtype run -i '{"days_until_due": 3}' 04_tools_and_function_calling.qtype.yaml
```

**Expected output:**

```json
{
  "deadline_formatted": "January 17, 2026 at 03:39 PM UTC"
}
```

The exact time will match when you run it, but the date should be 3 days from now.

---

### Try Different Durations

```bash
# One week deadline
qtype run -i '{"days_until_due": 7}' 04_tools_and_function_calling.qtype.yaml

# Two weeks
qtype run -i '{"days_until_due": 14}' 04_tools_and_function_calling.qtype.yaml

# Same day (0 days)
qtype run -i '{"days_until_due": 0}' 04_tools_and_function_calling.qtype.yaml
```

---

### Add the `--progress` Flag

For more visibility into tool execution:

```bash
qtype run -i '{"days_until_due": 3}' 04_tools_and_function_calling.qtype.yaml --progress
```

You'll see each step execute in real-time:

```
Step get_current_time     ✔ 1 succeeded
Step create_format_string ✔ 1 succeeded
Step add_days            ✔ 1 succeeded
Step format_deadline     ✔ 1 succeeded
```

---

## Part 4: Understanding Tools Deeply (Bonus)

### Tool Types and Custom Types

Remember from Tutorial 3 where `calculate_time_difference` returns `TimeDifferenceResultType`? That's a custom type defined in the commons library:

```yaml
types:
  - id: TimeDifferenceResultType
    properties:
      days: int
      seconds: int
      microseconds: int
      total_hours: float
      total_minutes: float
      total_seconds: float
      total_days: float
```

If you use `calculate_time_difference`, you can extract fields from its result:

```yaml
- id: calc_difference
  type: InvokeTool
  tool: qtype.application.commons.tools.calculate_time_difference
  input_bindings:
    start_time: start
    end_time: end
  output_bindings:
    result: time_diff  # time_diff is now TimeDifferenceResultType

# Later, access fields using FieldExtractor or Construct
```

---

### Generating Your Own Tools

When you're ready to create custom tools, use `qtype convert`:

**From a Python module:**

```bash
# Generate tools from all functions in myapp.utils
qtype convert python --module myapp.utils --output my_tools.qtype.yaml
```

QType will:
- Scan all public functions in the module
- Extract type hints from function signatures
- Generate tool definitions with proper input/output types
- Include docstrings as descriptions

**From an OpenAPI spec:**

```bash
# Generate tools from a REST API
qtype convert openapi --spec weather_api.yaml --output weather_tools.qtype.yaml
```

QType will:
- Parse endpoint definitions
- Create a tool for each operation
- Map request parameters to tool inputs
- Map response schemas to tool outputs
- Handle authentication configurations

<!-- **Learn more:** See the [How-To Guide: Generate Tools](../How-To%20Guides/Tools/generate-tools.md) for detailed examples. -->

---

## What You've Learned

Congratulations! You've mastered:

✅ **Tool concepts** - References to Python functions or API calls  
✅ **Importing tools** - Using `!include` with local or remote files  
✅ **InvokeTool step** - Calling tools with input/output bindings  
✅ **Input bindings** - Mapping flow variables to tool parameters  
✅ **Output bindings** - Mapping tool results to flow variables  
✅ **Tool chaining** - Connecting outputs to inputs across steps  
✅ **Commons library** - Pre-built tools for common operations  
✅ **Tool generation** - Using `qtype convert` to create tool definitions  

---

## Next Steps

**Reference the complete example:**

- [`04_tools_and_function_calling.qtype.yaml`](https://github.com/bazaarvoice/qtype/blob/main/examples/tutorials/04_tools_and_function_calling.qtype.yaml) - Full working example
- [Commons Library](https://github.com/bazaarvoice/qtype/blob/main/common/tools.qtype.yaml) - Browse all available tools
- [Commons Library Source](https://github.com/bazaarvoice/qtype/blob/v0.1.11/qtype/application/commons/tools.py) - Browse the source of tools.
<!-- 
**Learn more:**

- [PythonFunctionTool Reference](../components/PythonFunctionTool.md) - Complete specification
- [APITool Reference](../components/APITool.md) - External service integration
- [InvokeTool Step](../components/InvokeTool.md) - Advanced binding patterns
- [Generate Tools](../How-To%20Guides/Tools/generate-tools.md) - Create your own tools -->

<!-- **Next tutorial:**

- Tutorial 5: Building an AI Agent - Use tools with autonomous LLM decision-making -->

---

## Common Questions

**Q: Can I call multiple tools in parallel?**  
A: Not directly in a single step. However, if tools don't depend on each other's outputs, QType's execution engine may parallelize them automatically based on dependency analysis.

**Q: What happens if a tool raises an error?**  
A: The flow stops and returns an error. 

**Q: Can I pass literal values instead of variables to tools?**  
A: No - `input_bindings` only accepts variable names. Use PromptTemplate to create constant variables, or define them in your flow's input data.

**Q: How do I know what parameters a tool accepts?**  
A: Check the tool's YAML definition (in the commons library or your generated file). It lists all `inputs` with their types and whether they're optional.

**Q: Can tools modify variables or have side effects?**  
A: Tools are functional - they take inputs and return outputs without modifying flow state. Side effects (like writing files or calling APIs) happen inside the tool implementation, but they don't affect other flow variables.

**Q: What's the difference between InvokeTool and Agent?**  
A: **InvokeTool** explicitly calls a specific tool with defined bindings. **Agent** gives an LLM access to multiple tools and lets it decide which to use and when. Use InvokeTool for deterministic workflows, Agent for autonomous decision-making.
