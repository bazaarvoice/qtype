# LLMInference

LLMInference is a step that performs direct language model inference, sending prompts to AI models and capturing their responses. It provides the core interface for integrating large language models into QType workflows, supporting both simple text generation and complex conversational interactions.

LLMInference steps can maintain conversation context through memory, apply system prompts for role-setting, and handle various input formats to create flexible AI-powered applications.

## Rules and Behaviors

- **Required Model**: The `model` field is mandatory and specifies which model configuration to use for inference.
- **Automatic Output**: If no outputs are specified, automatically creates a single output variable named `{step_id}.response` of type `text`.
- **Memory Integration**: Can optionally reference a Memory object to maintain conversation history and context across multiple interactions.
- **System Message**: Optional `system_message` field sets the AI's role and behavior context.
- **Flexible Inputs**: Can accept any number of input variables that will be passed to the model.
- **Model Reference**: Can reference models by ID string or embed model configuration inline.

--8<-- "components/LLMInference.md"

## Related Concepts

LLMInference steps require [Model](../Concepts/model.md) configurations, may use [Memory](../Concepts/memory.md) for context retention, often consume output from [PromptTemplate](prompt-template.md) steps, and are extended by [Agent](agent.md) steps for tool-enabled interactions.

## Example Usage
