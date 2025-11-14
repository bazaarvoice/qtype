# Adding Tools and Function Calling

**Time:** 20 minutes  
**Prerequisites:** [Tutorial 1: Build Your First QType Application](01-first-qtype-application.md), [Tutorial 2: Build a Conversational Chatbot](02-conversational-chatbot.md)  
**Example:** [`time_utilities.qtype.yaml`](https://github.com/bazaarvoice/qtype/blob/main/examples/time_utilities.qtype.yaml)

**What you'll learn:** Extend your QType applications with tools - reusable functions that can perform calculations, call APIs, or execute custom logic.

**What you'll build:** A time zone calculator that uses a real-world API tool to calculate time differences between cities.

---

## What Are Tools?

**Tools** in QType are reusable functions that your flows can invoke. They extend your application's capabilities beyond just LLM inference.

Tools can be:

- **Python functions** - Call any Python code
- **API endpoints** - Make HTTP requests to external services

**Why use tools?**

- Get real-time data (current time, weather, stock prices)
- Perform calculations or data transformations
- Integrate with databases or external systems
- Reuse common functionality across multiple flows

---

## Part 1: Understanding the Commons Library (5 minutes)

QType includes a built-in library of common tools at `qtype.application.commons.tools`. Let's explore what's available.

### Generate the Commons Library

**Directory Structure:**

For this tutorial, we'll generate the commons library in a `common/` directory at the root of your project:

```
your-project/
├── common/              # Generated commons library
│   ├── tools.qtype.yaml
│   └── aws.bedrock.models.qtype.yaml
└── examples/            # Your tutorial files
    └── time_utilities.qtype.yaml
```

**Generate the files:**

From your project root, run:

```bash
qtype generate commons --prefix ./common/
```

This creates two files:

- `./common/tools.qtype.yaml` - All available Python function tools
- `./common/aws.bedrock.models.qtype.yaml` - AWS Bedrock model configurations

**Check your work:**

1. Look at `./common/tools.qtype.yaml`
2. Search for "get_current_timestamp"
3. You should see tool definitions with inputs and outputs

### Tools We'll Use Today

From the commons library, we'll use two time-related functions:

1. **`get_current_timestamp()`** - Returns current UTC time as datetime
2. **`timedelta(timestamp, hours=0, ...)`** - Adds/subtracts time from a timestamp
3. **`calculate_time_difference(start_time, end_time)`** - Calculates duration between two times

---

## Part 2: Create Your Application (5 minutes)

### Set Up the Basic Structure

Create a file called `time_utilities.qtype.yaml`:

```yaml
id: time_utilities
description: A simple application demonstrating tool usage

# Import the commons tools library
references:

- !include ../common/tools.qtype.yaml
```

**What's happening:**

- `references: - !include ...` - Imports tool definitions from another YAML file
- All tools from `tools.qtype.yaml` become available in your application
- Tools are referenced by their full IDs like `qtype.application.commons.tools.get_current_timestamp`

**Check your work:**

1. Save the file
2. Run: `qtype validate time_utilities.qtype.yaml`
3. Should pass ✅ (even with just these lines)

---

### Define Your Flow Variables

Add a flow with variables for each step's output:

```yaml
flows:

- type: Flow
    id: time_info_flow
    description: Get and format the current timestamp
    
    variables:

- id: current_time
        type: datetime
      - id: time_two_hours_later
        type: datetime
      - id: time_difference
        type: TimeDifferenceResultType
    
    outputs:

- current_time
      - time_difference
```

**What this means:**

- `variables:` - Declares all data used in the flow
- `datetime` type - QType's built-in type for timestamps
- `TimeDifferenceResultType` - A custom type from the commons library
- `outputs:` - Only these two variables are returned as final results

**Check your work:**

1. Validate: `qtype validate time_utilities.qtype.yaml`
2. Should still pass ✅

---

## Part 3: Add Tool Invocation Steps (10 minutes)

Now let's add steps that actually call our tools.

### Step 1: Get Current Timestamp

Add this step to your flow:

```yaml
    steps:
      # Step 1: Get current timestamp
      - id: get_time
        type: InvokeTool
        tool: qtype.application.commons.tools.get_current_timestamp
        input_bindings: {}
        output_bindings:
          result: current_time
```

**Breaking down InvokeTool:**

- `type: InvokeTool` - Step type for calling tools (new concept!)
- `tool: <full_tool_id>` - Reference to the tool we want to call
- `input_bindings: {}` - Maps flow variables to tool parameters (empty because this tool has no parameters)
- `output_bindings:` - Maps tool outputs back to flow variables
  - `result: current_time` - Tool returns `result`, we store it in `current_time`

---

### Step 2: Calculate Future Time

Add a step to calculate what time it will be in 2 hours:

```yaml
      # Step 2: Calculate time 2 hours from now
      - id: add_hours
        type: InvokeTool
        tool: qtype.application.commons.tools.timedelta
        input_bindings:
          timestamp: current_time
          hours: "2"
        output_bindings:
          result: time_two_hours_later
```

**What this does:**

- Takes our `current_time`
- Adds 2 hours to it using the `timedelta` tool
- Stores the result in `time_two_hours_later`

**Key concept:** Input bindings map flow variables to tool parameters. Here we're passing:

- `timestamp: current_time` - The variable from Step 1
- `hours: "2"` - The number of hours to add (as a string that will be converted to int)

---

### Step 3: Calculate Time Difference

Add a final step to calculate the difference:

```yaml
      # Step 3: Calculate the time difference
      - id: calc_difference
        type: InvokeTool
        tool: qtype.application.commons.tools.calculate_time_difference
        input_bindings:
          start_time: current_time
          end_time: time_two_hours_later
        output_bindings:
          result: time_difference
```

**What this does:**

- Compares `current_time` and `time_two_hours_later`
- Returns a structured object with the difference in seconds, minutes, hours, days
- Stores in `time_difference` (which has type `TimeDifferenceResultType`)

**Check your work:**

1. Validate: `qtype validate time_utilities.qtype.yaml`
2. Should pass ✅

---

## Part 4: Run Your Application (5 minutes)

### Test It!

Run your application:

```bash
qtype run time_utilities.qtype.yaml
```

**Expected output:**
```json
INFO: Executing workflow from examples/time_utilities.qtype.yaml
INFO: ✅ Flow execution completed successfully
INFO: Processed 1 input(s)
INFO: 
Results:
current_time: 2025-11-07 18:47:09.696270+00:00
time_difference: total_seconds=0.0 total_minutes=0.0 total_hours=0.0 total_days=0.0 days=0 seconds=0 microseconds=0
```

**What happened:**

1. QType called `get_current_timestamp()` and got the current UTC time
2. Added 2 hours to create a future timestamp
3. Calculated the difference between the two times
4. Returned only the outputs we specified (`current_time` and `time_difference`)

---

## How Tool Invocation Works

When QType executes an `InvokeTool` step:

```
1. Resolve the tool
   ↓
2. Prepare inputs (map variables → tool parameters)
   ↓
3. Validate input types
   ↓
4. Execute the function
   ↓
5. Capture outputs
   ↓
6. Map outputs → flow variables
   ↓
7. Type conversion (to QType types)
```

**Key insight:** Tools are just Python functions. QType:

- Handles importing the module
- Validates all types match
- Converts between Python and QType types automatically
- Manages data flow between steps

---

## What You've Learned

Congratulations! You've mastered:

✅ **Tool concepts** - What tools are and why they're useful  
✅ **Commons library** - Built-in tools available in QType  
✅ **InvokeTool step** - How to call tools from flows  
✅ **Input/output bindings** - Mapping variables to tool parameters  
✅ **Sequential tool chains** - Passing data between multiple tools  

---

## Tool Types in QType

QType supports two types of tools:

### PythonFunctionTool

Calls a Python function from a module:

```yaml
tools:

- type: PythonFunctionTool
    id: my_calculator
    name: calculate
    description: Performs mathematical calculations
    function_name: calculate
    module_path: my_tools.math
    inputs:
      expression:
        type: text
        optional: false
    outputs:
      result:
        type: float
        optional: false
```

### APITool

Calls an HTTP API endpoint:

```yaml
tools:

- type: APITool
    id: weather_api
    name: get_weather
    description: Fetches weather data
    endpoint: https://api.weather.com/current
    method: GET
    auth: weather_api_key
    inputs:
      location:
        type: text
    outputs:
      temperature:
        type: float
```

---

## Common Patterns

### Pattern 1: Sequential Tool Calls

Chain tools where each step uses the previous output (like our example):

```yaml
steps:

- type: InvokeTool
    tool: fetch_data
    output_bindings: {result: raw_data}
  
  - type: InvokeTool
    tool: process_data
    input_bindings: {data: raw_data}
    output_bindings: {result: processed_data}
  
  - type: InvokeTool
    tool: save_data
    input_bindings: {data: processed_data}
```

### Pattern 2: Using Variables from Flow Inputs

Pass flow input variables to tools:

```yaml
flows:

- type: Flow
    id: timezone_converter
    variables:

- id: user_timezone
        type: text
      - id: current_time
        type: datetime
      - id: converted_time
        type: datetime
    inputs:

- user_timezone
    steps:

- type: InvokeTool
        tool: get_current_timestamp
        output_bindings: {result: current_time}
      
      - type: InvokeTool
        tool: convert_timezone
        input_bindings:
          timestamp: current_time
          timezone: user_timezone
        output_bindings: {result: converted_time}
```

### Pattern 3: Optional Parameters

Tools can have optional parameters (use defaults if not provided):

```yaml
input_bindings:
  timestamp: current_time
  # hours parameter is optional, defaults to 0
```

---

## Next Steps

**Reference the complete example:**

- [`time_utilities.qtype.yaml`](https://github.com/bazaarvoice/qtype/blob/main/examples/time_utilities.qtype.yaml) - Full working example

**Learn more:**

- [Tool Concept](../Concepts/Core/tool.md) - Full tool architecture
- [InvokeTool Step](../components/InvokeTool.md) - Complete API reference
- [Create Python Tools](../How-To%20Guides/Tools/python-tools.md) - Build your own tools
- [Create API Tools](../How-To%20Guides/Tools/api-tools.md) - Integrate external APIs

---

## Common Questions

**Q: Do I need to generate the commons library every time?**  
A: No, only once. The generated files (`./common/tools.qtype.yaml`) can be committed to your repository and reused.

**Q: Can I create my own tools?**  
A: Yes! Use `qtype convert module` to convert any Python module to QType tools. See the [Python Tools guide](../How-To%20Guides/Tools/python-tools.md).

**Q: What's the difference between InvokeTool and Agent?**  
A: `InvokeTool` explicitly calls one specific tool. `Agent` (covered in a later tutorial) lets the LLM decide which tools to call based on the task.

**Q: Can tools call other tools?**  
A: Not directly. Tools are just functions. But your flow can chain multiple `InvokeTool` steps together.

**Q: What types can I use in tool parameters?**  
A: Any QType primitive type (`text`, `int`, `float`, `bool`, `datetime`) or custom types you define. See [Variable Types](../Concepts/Core/variable.md).

**Q: How do I handle errors from tools?**  
A: Tools that raise exceptions will stop the flow. Use `qtype run --log-level DEBUG` to see detailed error information.
