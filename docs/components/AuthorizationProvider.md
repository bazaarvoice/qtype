### AuthorizationProvider

Defines how tools or providers authenticate with APIs, such as OAuth2 or API keys.

- **id** (`str`): Unique ID of the authorization configuration.
- **api_key** (`str | None`): API key if using token-based auth.
- **client_id** (`str | None`): OAuth2 client ID.
- **client_secret** (`str | None`): OAuth2 client secret.
- **host** (`str | None`): Base URL or domain of the provider.
- **scopes** (`list[str] | None`): OAuth2 scopes required.
- **token_url** (`str | None`): Token endpoint URL.
- **type** (`str`): Authorization method, e.g., 'oauth2' or 'api_key'.
