# Variable

Variables are the fundamental data containers in QType. All data flowing between [Steps](Steps/index.md) must be explicitly declared as variables. This "declare before use" principle creates clear data contracts and enables static validation.

## Variable Scoping

Variables are scoped to the [Flow](flow.md) where they are declared. Each flow's `variables` section lists all variables available within that flow.

```yaml
flows:
  - type: Flow
    id: my_flow
    variables:
      - id: user_input
        type: text
      - id: processed_output
        type: text
```

## Variable Declaration

Each variable must have:
- **Unique ID**: Used to reference the variable throughout the flow. Must be unique within the flow's scope.
- **Type**: Specifies the data type (primitive, domain-specific, or custom type).

## Referencing Variables

Steps reference variables by their ID (as a string):

```yaml
steps:
  - id: my_step
    type: LLMInference
    inputs:
      - user_input  # References the variable declared above
    outputs:
      - processed_output
```

The validator ensures that all referenced variables are declared in the flow's `variables` section.

--8<-- "components/Variable.md"

--8<-- "components/PrimitiveTypeEnum.md"

## Domain Specific Types

Domain specific types are included for common use cases (chat bots, RAG, etc)


--8<-- "components/ChatMessage.md"
--8<-- "components/ChatContent.md"
--8<-- "components/Embedding.md"
