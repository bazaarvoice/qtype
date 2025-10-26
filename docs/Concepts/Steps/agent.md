# Agent

Agent is a specialized LLMInference step that combines language model capabilities with tool access, enabling AI assistants that can perform actions, make API calls, execute functions, and interact with external systems. Agents represent autonomous AI entities that can reason about tasks and use available tools to accomplish objectives.

Agents extend the basic LLMInference functionality by providing access to a curated set of tools, allowing the AI to move beyond text generation to actual task execution and problem-solving.

## Key Principles

### Tool References by ID

Agents reference tools by their IDs (as strings):

```yaml
tools:
  - type: PythonFunctionTool
    id: calculator
    name: calculate
    # ... tool config

flows:
  - type: Flow
    id: agent_flow
    steps:
      - type: Agent
        id: my_agent
        model: gpt4
        tools:
          - calculator  # References tool by ID
```

### Inherits from LLMInference

Agents have all the capabilities of LLMInference steps, including:
- Model reference by ID
- Memory integration by ID
- System message support
- Explicit variable declarations for inputs/outputs

## Rules and Behaviors

- **Inherits LLMInference**: All LLMInference rules and behaviors apply (required model, explicit variables, memory integration, etc.).
- **Required Model**: Must reference a model ID defined in the application.
- **Optional Tools**: The `tools` field lists tool IDs available to the agent (defaults to empty list).
- **Tool Integration**: References tools by ID string (tools must be defined in the application).
- **Decision Making**: The agent autonomously decides which tools to use based on the input and conversation context.
- **Multi-Step Execution**: Can perform multiple tool calls and reasoning steps within a single agent invocation.

--8<-- "components/Agent.md"

## Related Concepts

Agent steps extend [LLMInference](llm-inference.md) and require [Model](../Concepts/model.md) configurations and [Tool](../Concepts/tool.md) access. They may use [Memory](../Concepts/memory.md) for persistent context and can be orchestrated within [Flows](../Concepts/flow.md).

## Example Usage
