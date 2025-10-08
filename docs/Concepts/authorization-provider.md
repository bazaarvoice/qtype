# AuthorizationProvider

AuthorizationProvider defines how QType components authenticate with external APIs and services. It provides a centralized, reusable way to configure authentication credentials and methods for models, tools, indexes, and other components that need to access external resources.

By centralizing authentication configuration, AuthorizationProvider enables secure credential management, supports multiple authentication methods (API keys, OAuth2, Bearer tokens, AWS credentials), and allows the same credentials to be reused across multiple components.

## Key Principles

### Type Discriminator

All authorization providers must include a `type` field for proper schema validation:
- `type: APIKeyAuthProvider` for API key authentication
- `type: BearerTokenAuthProvider` for bearer token authentication
- `type: OAuth2AuthProvider` for OAuth2 authentication
- `type: AWSAuthProvider` for AWS credentials

### Centralized Definition & Reference by ID

Authorization providers are defined at the application level and referenced by ID:

```yaml
authorization_providers:
  - type: APIKeyAuthProvider
    id: openai_auth
    api_key: ${OPENAI_API_KEY}

models:
  - type: Model
    id: gpt4
    provider: openai
    auth: openai_auth  # References by ID
```

## Rules and Behaviors

- **Unique IDs**: Each authorization provider must have a unique `id` within the application. Duplicate authorization provider IDs will result in a validation error.
- **Required Type**: The `type` field is mandatory and specifies the authentication method.
- **Method-Specific Fields**: Different authentication types require different field combinations (see component docs for details).
- **Reference by Components**: Can be referenced by Models, Tools, Indexes, and TelemetrySink by their ID string.
- **Environment Variable Support**: Credential fields support environment variable substitution using `${VARIABLE_NAME}` syntax for secure credential management.

--8<-- "components/AuthorizationProvider.md"

## Related Concepts

AuthorizationProvider is referenced by [Model](model.md), [Tool](tool.md), [Index](index.md), and other components that need external API access.

## Example Usage
