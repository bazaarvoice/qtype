# Building an Agentic Chatbot

This example shows how to create an AI agent that can use tools to answer questions. Unlike a simple chatbot that only generates text, an agent can call functions to get real-time information and perform actions.

We'll build a chatbot that can answer questions about time and dates by using Python functions as tools.

## What is an Agent?

An **Agent** is an AI that can:

- Reason about which tools to use
- Call those tools with the right parameters
- Use the results to formulate a final answer

This makes agents much more capable than traditional chatbots for tasks that require real-world information or actions.

## Step 1: Define the Model

First, we'll set up our language model. We're using Amazon Nova Lite through AWS Bedrock:

```yaml
id: simple_agent
description: A simple agent chatbot with time and date tools
models:
  - type: Model
    id: nova_lite
    provider: aws-bedrock
    model_id: amazon.nova-lite-v1:0
    inference_params:
      temperature: 0.7
      max_tokens: 512
```

**Key Points:**

- `provider: aws-bedrock` - Uses AWS Bedrock (requires AWS credentials configured)
- `temperature: 0.7` - Moderate creativity in responses
- `max_tokens: 512` - Limits response length

## Step 2: Define the Tools

Tools are Python functions that the agent can call. Let's add three time-related tools:

```yaml
tools:
  - type: PythonFunctionTool
    id: get_current_timestamp
    name: get_current_timestamp
    description: Get the current UTC timestamp
    function_name: get_current_timestamp
    module_path: qtype.application.commons.tools
    inputs: {}
    outputs:
      result:
        type: datetime
        optional: false
        
  - type: PythonFunctionTool
    id: format_datetime
    name: format_datetime
    description: Format a timestamp using a custom format string
    function_name: format_datetime
    module_path: qtype.application.commons.tools
    inputs:
      timestamp:
        type: datetime
        optional: false
      format_string:
        type: text
        optional: false
    outputs:
      result:
        type: text
        optional: false
        
  - type: PythonFunctionTool
    id: timedelta
    name: timedelta
    description: Add a specified amount of time from a given timestamp
    function_name: timedelta
    module_path: qtype.application.commons.tools
    inputs:
      timestamp:
        type: datetime
        optional: false
      days:
        type: int
        optional: true
      hours:
        type: int
        optional: true
      minutes:
        type: int
        optional: true
      seconds:
        type: int
        optional: true
    outputs:
      result:
        type: datetime
        optional: false
```

**Important:** Each tool needs:

- `id` - Unique identifier
- `name` - Display name for the agent
- `description` - Tells the agent what the tool does (this is crucial!)
- `function_name` - The actual Python function to call
- `module_path` - Where to find the function
- `inputs`/`outputs` - Type definitions for parameters

The agent reads the `description` to decide when to use each tool.

### Using Shared Tool Libraries

Instead of defining tools inline, you can reference a shared library using `!include`:

```yaml
# Include tools from common library
references:
  - !include ../common/tools.qtype.yaml

# Then reference tools by their full IDs
steps:
  - type: Agent
    tools:
      - qtype.application.commons.tools.get_current_timestamp
      - qtype.application.commons.tools.format_datetime
```

This approach promotes reusability and keeps your specifications clean. See [File Inclusion](../Getting%20Started/How%20To/01-file-inclusion.md) for more details.

## Step 3: Add Memory

Memory allows the agent to remember the conversation history:

```yaml
memories:
  - id: chat_memory
    token_limit: 10000
```

This stores up to 10,000 tokens of conversation history.

## Step 4: Create the Agent Flow

Now we define the conversational flow with our agent:

```yaml
flows:
  - type: Flow
    id: agent_chat
    interface:
      type: Conversational
    variables:
      - id: user_message
        type: ChatMessage
      - id: response
        type: ChatMessage
    inputs:
      - user_message
    outputs:
      - response
    steps:
      - id: agent_step
        type: Agent
        model: nova_lite
        system_message: "You are a helpful assistant with access to time and date tools. Use them when users ask about time-related information."
        memory: chat_memory
        tools:
          - get_current_timestamp
          - format_datetime
          - timedelta
        inputs:
          - user_message
        outputs:
          - response
```

**Key Differences from LLMInference:**

- `type: Agent` - Uses the Agent step (not LLMInference)
- `tools: [...]` - List of tools the agent can use
- `system_message` - Instructs the agent on how to use the tools
- `interface: type: Conversational` - Makes this a chatbot interface

The agent will automatically:

1. Read the user's message
2. Decide if it needs to call any tools
3. Call the tools if needed
4. Formulate a response using the tool results

## Step 5: Add Telemetry (Optional)

Track your agent's behavior with OpenTelemetry:

```yaml
telemetry:
  id: simple_agent_telemetry
  endpoint: http://localhost:6006/v1/traces
```

You can view traces by running:

```bash
phoenix serve
```

Then visit [http://localhost:6006](http://localhost:6006)

## Complete Example

Here's the full YAML file:

```yaml
--8<-- "../examples/simple_agent.qtype.yaml"
```

You can download it [here](https://github.com/bazaarvoice/qtype/blob/main/examples/simple_agent.qtype.yaml).

## Running the Agent

### Prerequisites

- AWS credentials configured (for Bedrock access)
- (Optional) Phoenix running for telemetry: `phoenix serve`

### Start the Server

```bash
qtype serve examples/simple_agent.qtype.yaml
```

### Open the Chat UI

Visit [http://localhost:8000/ui](http://localhost:8000/ui)

## Try It Out

Ask your agent questions like:

- "What time is it right now?"
- "What will the time be in 3 hours?"
- "Format the current time like '2024-03-15 at 2:30 PM'"

Watch how the agent:

1. Understands your question
2. Decides which tools to use
3. Calls the tools with the right parameters
4. Combines the results into a natural response

## How Agents Work

Behind the scenes, the agent follows a **ReAct** (Reasoning + Acting) pattern:

1. **Think** - Reasons about what to do
2. **Act** - Calls a tool if needed
3. **Observe** - Gets the tool result
4. **Repeat** - Continues until it has a final answer

This happens automatically - you just provide the tools and system message!

## Learn More

- [Tool Concepts](../Concepts/tool.md) - Deep dive into creating and using tools
- [Agent API Reference](../components/Agent.md) - Full Agent configuration options
- [Memory Configuration](../components/Memory.md) - Advanced memory management

## Next Steps

Try adding your own tools:

- API calls to external services
- Database queries
- File operations
- Custom business logic

The agent can orchestrate any Python function you provide!
