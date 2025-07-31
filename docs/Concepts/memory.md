# Memory

Memory in QType provides persistent storage for conversation history and contextual state data across multiple steps or conversation turns. It enables applications to maintain context between interactions, allowing for more coherent and context-aware conversations in chatbots, agents, and multi-turn workflows.

Memory is particularly useful for maintaining chat history, storing previous outputs, and preserving important context that should persist across different steps in a flow or across multiple invocations of an application.

## Rules and Behaviors

- **Unique IDs**: Each memory block must have a unique `id` within the application. Duplicate memory IDs will result in a validation error.
- **Token Management**: Memory automatically manages token limits to prevent exceeding model context windows. When the token limit is reached, older content is flushed based on the `token_flush_size`.
- **Chat History Ratio**: The `chat_history_token_ratio` determines what portion of the total memory should be reserved for chat history versus other contextual data.
- **Default Values**: Memory has sensible defaults - 100,000 token limit, 70% chat history ratio, and 3,000 token flush size.
- **Reference by Steps**: Memory can be referenced by `LLMInference` and `Agent` steps to maintain context across interactions.

--8<-- "components/Memory.md"

## Related Concepts

Memory is primarily used by LLM-based steps like [LLMInference](llm-inference.md) and [Agent](agent.md) to maintain conversational context.

## Example Usage

