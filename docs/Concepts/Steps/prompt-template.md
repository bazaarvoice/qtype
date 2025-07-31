# PromptTemplate

PromptTemplate is a step that generates dynamic prompts by substituting variables into string templates. It enables the creation of reusable prompt patterns that can be customized with different inputs, making it easy to build flexible prompt-driven workflows.

PromptTemplate steps are particularly useful for preprocessing inputs before sending them to language models, creating consistent prompt formats across different use cases, and building modular prompt libraries that can be shared across applications.

## Rules and Behaviors

- **Required Template**: The `template` field is mandatory and contains the string template with variable placeholders.
- **Variable Substitution**: Uses standard string formatting with curly braces `{variable_name}` for variable placeholders.
- **Automatic Output**: If no outputs are specified, automatically creates a single output variable named `{step_id}.prompt` of type `text`.
- **Single Output Requirement**: Must have exactly one output variable - validation error occurs if multiple outputs are defined.
- **Input Flexibility**: Can accept any number of input variables that correspond to template placeholders.

--8<-- "components/PromptTemplate.md"

## Related Concepts

PromptTemplate steps are often used before [LLMInference](llm-inference.md) or [Agent](agent.md) steps to prepare prompts, and they consume [Variables](../Concepts/variable.md) for dynamic content generation.

## Example Usage
