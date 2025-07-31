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

### Basic Memory Configuration

```yaml
id: chat_app

memories:
  - id: chat_memory
    token_limit: 50000
    chat_history_token_ratio: 0.8
    token_flush_size: 2000

flows:
  - id: conversation_flow
    steps:
      - id: chat_response
        model: gpt-4o
        memory: chat_memory
        system_message: "You are a helpful assistant that remembers our conversation."
        inputs:
          - id: user_message
            type: text
        outputs:
          - id: assistant_response
            type: text
```

### Embedded Memory Configuration

Memory can also be defined inline within steps:

```yaml
flows:
  - id: inline_memory_example
    steps:
      - id: persistent_chat
        model: claude-3
        memory:
          id: session_memory
          token_limit: 75000
          chat_history_token_ratio: 0.9
        system_message: "Remember our previous interactions and build upon them."
        inputs:
          - id: query
            type: text
        outputs:
          - id: contextual_response
            type: text
```

### Agent with Memory

```yaml
memories:
  - id: agent_memory
    token_limit: 100000

flows:
  - id: agent_workflow
    steps:
      - id: smart_agent
        model: gpt-4o
        memory: agent_memory
        tools: [search_tool, calculator_tool]
        system_message: |
          You are a research assistant. Use your tools to help answer questions
          and remember what we've discussed previously.
        inputs:
          - id: research_question
            type: text
        outputs:
          - id: research_answer
            type: text
```

### Memory for Multi-Step Workflows

```yaml
memories:
  - id: workflow_memory
    token_limit: 80000
    chat_history_token_ratio: 0.6

flows:
  - id: multi_step_analysis
    steps:
      - id: analyze_data
        model: gpt-4o
        memory: workflow_memory
        inputs:
          - id: raw_data
            type: text
        outputs:
          - id: analysis
            type: text
      
      - id: generate_report
        model: gpt-4o
        memory: workflow_memory  # Same memory to maintain context
        system_message: "Generate a report based on the previous analysis."
        inputs:
          - id: report_requirements
            type: text
        outputs:
          - id: final_report
            type: text
```
