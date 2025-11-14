# Memory

Memory in QType provides persistent storage for conversation history and contextual state data across multiple steps or conversation turns. It enables applications to maintain context between interactions, allowing for more coherent and context-aware conversations in chatbots, agents, and multi-turn workflows.

Memory configurations are defined at the application level and referenced by steps that need to maintain state.

## Key Principles

### Centralized Definition

Memory objects are defined once at the application level and can be shared across multiple steps:

```yaml
id: my_app
memories:
  - id: chat_memory
    token_limit: 50000
    chat_history_token_ratio: 0.7

flows:
  - type: Flow
    id: chat_flow
    steps:
      - type: LLMInference
        model: gpt4
        memory: chat_memory  # References by ID
```

### Reference by ID

Steps reference memory configurations by their ID (as a string), not by embedding the memory object inline.

## Rules and Behaviors

- **Unique IDs**: Each memory block must have a unique `id` within the application. Duplicate memory IDs will result in a validation error.
- **Token Management**: Memory automatically manages token limits to prevent exceeding model context windows. When the token limit is reached, older content is flushed based on the `token_flush_size`.
- **Chat History Ratio**: The `chat_history_token_ratio` determines what portion of the total memory should be reserved for chat history versus other contextual data.
- **Default Values**: Memory has sensible defaults - 100,000 token limit, 70% chat history ratio, and 3,000 token flush size.
- **Shared Memory**: Multiple steps can reference the same memory ID to share conversational context.

--8<-- "components/Memory.md"

## Related Concepts

Memory is primarily used by LLM-based steps like [LLMInference](../Steps/llm-inference.md) and [Agent](../Steps/agent.md) to maintain conversational context.

## Example Usage

