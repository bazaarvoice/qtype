# AuthorizationProvider

AuthorizationProvider defines how QType components authenticate with external APIs and services. It provides a centralized, reusable way to configure authentication credentials and methods for models, tools, indexes, and other components that need to access external resources.

By centralizing authentication configuration, AuthorizationProvider enables secure credential management, supports multiple authentication methods (API keys, OAuth2, etc.), and allows the same credentials to be reused across multiple components without duplication.

## Rules and Behaviors

- **Unique IDs**: Each authorization provider must have a unique `id` within the application. Duplicate authorization provider IDs will result in a validation error.
- **Required Type**: The `type` field is mandatory and specifies the authentication method (e.g., "api_key", "oauth2").
- **Method-Specific Fields**: Different authentication types require different field combinations:
  - API key authentication: requires `api_key` field
  - OAuth2 authentication: typically requires `client_id`, `client_secret`, `token_url`, and optionally `scopes`
- **Optional Host**: The `host` field can specify the base URL or domain of the service provider.
- **Reference by Components**: Can be referenced by Models, Tools, Indexes, and TelemetrySink by ID string or embedded as inline objects.
- **Environment Variable Support**: Credential fields support environment variable substitution using `${VARIABLE_NAME}` syntax.

--8<-- "components/AuthorizationProvider.md"

## Related Concepts

AuthorizationProvider is referenced by [Model](model.md), [Tool](tool.md), [Index](index.md), and other components that need external API access.

## Example Usage
