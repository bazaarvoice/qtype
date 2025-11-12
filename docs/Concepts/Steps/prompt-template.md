# PromptTemplate

PromptTemplate is a step that generates dynamic prompts by substituting variables into string templates. It enables the creation of reusable prompt patterns that can be customized with different inputs, making it easy to build flexible prompt-driven workflows.

PromptTemplate steps are particularly useful for preprocessing inputs before sending them to language models, creating consistent prompt formats across different use cases, and building modular prompt libraries.

## Key Principles

### Explicit Variable Declaration

All inputs and outputs must be declared in the flow's `variables` section:

```yaml
flows:
  - type: Flow
    id: my_flow
    variables:
      - id: user_name
        type: text
      - id: generated_prompt
        type: text
    steps:
      - type: PromptTemplate
        id: greeting_prompt
        template: "Hello {user_name}, how can I help you today?"
        inputs:
          - user_name
        outputs:
          - generated_prompt
```

### Variable Substitution

Uses standard string formatting with curly braces `{variable_name}` for placeholders. The variable names in the template must match the IDs of input variables.

## Rules and Behaviors

- **Required Template**: The `template` field is mandatory and contains the string template with variable placeholders.
- **Required Variables**: All inputs and outputs must be declared in the flow's `variables` section.
- **Variable Substitution**: Template placeholders must correspond to input variable IDs.
- **Input Flexibility**: Can accept any number of input variables that correspond to template placeholders.

--8<-- "components/PromptTemplate.md"

## Related Concepts

PromptTemplate steps are often used before [LLMInference](llm-inference.md) or [Agent](agent.md) steps to prepare prompts, and they consume [Variables](../Core/variable.md) for dynamic content generation.

## Example Usage
