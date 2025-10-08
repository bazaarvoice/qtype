# Model

A model represents a generative AI model configuration that can be used for inference tasks such as text generation, chat, or embeddings. Models define how to connect to and configure specific AI providers like OpenAI, Anthropic, AWS Bedrock, or others.

Each model must have a unique `id` and specify a `provider`. Models are defined at the application level and can be referenced by steps like `LLMInference`, `Agent`, or `InvokeEmbedding`.

## Key Principles

### Type Discriminator

All models must include a `type` field for proper schema validation:
- `type: Model` for standard generative models
- `type: EmbeddingModel` for embedding/vectorization models

### Referencing Models

Steps reference models by their ID:

```yaml
models:
  - type: Model
    id: gpt4
    provider: openai
    model_id: gpt-4-turbo

flows:
  - type: Flow
    id: my_flow
    steps:
      - type: LLMInference
        model: gpt4  # References the model by ID
```

## Rules and Behaviors

- **Unique IDs**: Each model must have a unique `id` within the application. Duplicate model IDs will result in a validation error.
- **Model ID Resolution**: If `model_id` is not specified, the model's `id` field is used as the model identifier for the provider.
- **Provider Requirement**: The `provider` field is required and specifies which AI service to use (e.g., "openai", "anthropic", "aws-bedrock").
- **Authentication**: Models can reference an `AuthorizationProvider` by ID or as a string reference for API authentication.
- **Inference Parameters**: The `inference_params` dictionary allows customization of model behavior (temperature, max_tokens, etc.).

## Model Types

--8<-- "components/Model.md"

--8<-- "components/EmbeddingModel.md"

## Related Concepts

Models can reference [AuthorizationProvider](authorization-provider.md) for secure API access.

## Example Usage

