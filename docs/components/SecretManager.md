### SecretManager

Base class for secret manager configurations.

- **id** (`str`): Unique ID for this secret manager configuration.
- **type** (`str`): The type of secret manager.
- **auth** (`Reference[AuthProviderType] | str`): AuthorizationProvider used to access this secret manager.
