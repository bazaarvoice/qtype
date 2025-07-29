# Model

Describes a generative model configuration, including provider and model ID.

## Members
- **id** (`str`): Unique ID for the model.
- **auth** (`AuthorizationProvider | str | None`): AuthorizationProvider used for model access.
- **inference_params** (`dict[str, Any] | None`): Optional inference parameters like temperature or max_tokens.
- **model_id** (`str | None`): The specific model name or ID for the provider. If None, id is used
- **provider** (`str`): Name of the provider, e.g., openai or anthropic.

---
