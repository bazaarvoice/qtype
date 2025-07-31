# Model

A model represents a generative AI model configuration that can be used for inference tasks such as text generation, chat, or embeddings. Models define how to connect to and configure specific AI providers like OpenAI, Anthropic, AWS Bedrock, or others.

Each model must have a unique `id` and specify a `provider`. The model acts as a reusable configuration that can be referenced by steps like `LLMInference`, `Agent`, or vector search operations.

## Rules and Behaviors

- **Unique IDs**: Each model must have a unique `id` within the application. Duplicate model IDs will result in a validation error.
- **Model ID Resolution**: If `model_id` is not specified, the model's `id` field is used as the model identifier for the provider.
- **Provider Requirement**: The `provider` field is required and specifies which AI service to use (e.g., "openai", "anthropic", "aws-bedrock").
- **Authentication**: Models can reference an `AuthorizationProvider` for API authentication, either by ID reference or as an embedded object.
- **Inference Parameters**: Optional `inference_params` allow customization of model behavior (temperature, max_tokens, etc.) that are passed to the provider's API.

## Model Types

--8<-- "components/Model.md"

--8<-- "components/EmbeddingModel.md"

## Related Concepts

Models can reference [AuthorizationProvider](authorization-provider.md) for secure API access.

## Example Usage

### Basic Text Generation Model

```yaml
id: my_app

models:
  - id: gpt-4o
    provider: openai
    model_id: gpt-4o-mini
    auth: openai_auth
    inference_params:
      temperature: 0.7
      max_tokens: 1000

auths:
  - id: openai_auth
    type: api_key
    api_key: ${OPENAI_API_KEY}

flows:
  - id: text_generation
    steps:
      - id: generate_text
        model: gpt-4o
        system_message: "You are a helpful assistant."
        inputs:
          - id: user_prompt
            type: text
        outputs:
          - id: generated_text
            type: text
```

### Embedded Model Configuration

Models can also be defined inline within steps:

```yaml
flows:
  - id: inline_model_example
    steps:
      - id: chat_step
        model:
          id: claude-3
          provider: anthropic
          auth:
            id: anthropic_auth
            type: api_key
            api_key: ${ANTHROPIC_API_KEY}
          inference_params:
            temperature: 0.3
        inputs:
          - id: message
            type: text
        outputs:
          - id: response
            type: text
```

### Embedding Model Example

```yaml
models:
  - id: text_embeddings
    provider: openai
    model_id: text-embedding-3-small
    dimensions: 1536
    auth: openai_auth

flows:
  - id: vector_search_flow
    steps:
      - id: embed_query
        embedding_model: text_embeddings
        inputs:
          - id: search_query
            type: text
        outputs:
          - id: query_embedding
            type: Embedding
```
