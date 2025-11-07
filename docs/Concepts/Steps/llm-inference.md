# LLMInference

LLMInference is a step that performs direct language model inference, sending prompts to AI models and capturing their responses. It provides the core interface for integrating large language models into QType workflows, supporting both simple text generation and complex conversational interactions.

LLMInference steps can maintain conversation context through memory, apply system prompts for role-setting, and process inputs/outputs concurrently when configured.

## Key Principles

### Explicit Variable Declaration

All inputs and outputs must be declared in the flow's `variables` section and referenced by ID:

```yaml
flows:
  - type: Flow
    id: my_flow
    variables:
      - id: user_prompt
        type: text
      - id: ai_response
        type: text
    steps:
      - type: LLMInference
        id: llm_step
        model: gpt4
        inputs:
          - user_prompt  # References declared variable
        outputs:
          - ai_response
```

### Model Reference by ID

The `model` field references a model by its ID (as a string):

```yaml
models:
  - type: Model
    id: gpt4
    provider: openai

flows:
  - steps:
      - type: LLMInference
        model: gpt4  # String reference to model ID
```

## Rules and Behaviors

- **Required Model**: The `model` field is mandatory and must reference a model ID defined in the application.
- **Required Variables**: All inputs and outputs must be declared in the flow's `variables` section.
- **Memory Integration**: Can optionally reference a Memory object by ID to maintain conversation history and context.
- **System Message**: Optional `system_message` field sets the AI's role and behavior context.
- **Concurrency Support**: Supports `concurrency_config` for processing multiple inputs concurrently.

--8<-- "components/LLMInference.md"

## Related Concepts

LLMInference steps require [Model](../Core/model.md) configurations, may use [Memory](../Core/memory.md) for context retention, often consume output from [PromptTemplate](prompt-template.md) steps, and are extended by [Agent](agent.md) steps for tool-enabled interactions.

## Example Usage
