# Agent

Agent is a specialized LLMInference step that combines language model capabilities with tool access, enabling AI assistants that can perform actions, make API calls, execute functions, and interact with external systems. Agents represent autonomous AI entities that can reason about tasks and use available tools to accomplish objectives.

Agents extend the basic LLMInference functionality by providing access to a curated set of tools, allowing the AI to move beyond text generation to actual task execution and problem-solving in dynamic environments.

## Rules and Behaviors

- **Inherits LLMInference**: All LLMInference rules and behaviors apply (required model, automatic output, memory integration, etc.).
- **Required Tools**: The `tools` field is mandatory and specifies the list of tools available to the agent.
- **Tool Integration**: Can reference tools by ID string or embed tool configurations inline.
- **Decision Making**: The agent autonomously decides which tools to use based on the input and conversation context.
- **Multi-Step Execution**: Can perform multiple tool calls and reasoning steps within a single agent invocation.
- **Memory Awareness**: Leverages memory to maintain context across tool usage and conversations.

--8<-- "components/Agent.md"

## Related Concepts

Agent steps extend [LLMInference](llm-inference.md) and require [Model](../Concepts/model.md) configurations and [Tool](../Concepts/tool.md) access. They may use [Memory](../Concepts/memory.md) for persistent context and can be orchestrated within [Flows](../Concepts/flow.md).

## Example Usage
