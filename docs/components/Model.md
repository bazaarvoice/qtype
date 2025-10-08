### Model

Describes a generative model configuration, including provider and model ID.

- **type** (`Literal`): (No documentation available.)
- **id** (`str`): Unique ID for the model.
- **auth** (`Reference[AuthProviderType] | str | None`): AuthorizationProvider used for model access.
- **inference_params** (`dict[str, Any]`): Optional inference parameters like temperature or max_tokens.
- **model_id** (`str | None`): The specific model name or ID for the provider. If None, id is used
- **provider** (`str`): Name of the provider, e.g., openai or anthropic.
