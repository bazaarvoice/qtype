# Reference Entities by ID

Use QType's "define once, reference by ID" pattern to eliminate duplication and improve maintainability by assigning unique IDs to components and referencing them throughout your application.

### QType YAML

```yaml
# Define components with unique IDs
auths:
  - type: api_key
    id: openai_auth
    api_key: ${OPENAI_KEY}

models:
  - type: Model
    id: gpt4
    provider: openai
    model_id: gpt-4o
    auth: openai_auth  # Reference auth by ID

memories:
  - id: conversation_memory
    token_limit: 10000

flows:
  - type: Flow
    id: chat_flow
    steps:
      - type: LLMInference
        model: gpt4             # Reference model by ID
        memory: conversation_memory  # Reference memory by ID
```

### Explanation

- **`id` field**: Assigns a unique identifier to any component (models, auths, tools, variables, etc.)
- **Reference by string**: Use the ID string wherever the component is needed
- **Automatic resolution**: QType's linker automatically resolves ID references to actual objects during validation
- **Reusability**: The same component can be referenced multiple times throughout the application

## Complete Example

```yaml
!include ../../examples/conversational_ai/simple_chatbot.qtype.yaml
```

## See Also

- [Include QType YAML](include_qtype_yaml.md)
- [Tutorial: Your First QType Application](../../Tutorials/01-first-qtype-application.md)
- [Application Reference](../../components/Application.md)
