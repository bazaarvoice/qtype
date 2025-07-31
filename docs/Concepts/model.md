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

