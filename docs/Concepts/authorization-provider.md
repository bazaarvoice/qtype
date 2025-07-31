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

### API Key Authentication

```yaml
id: api_services_app

auths:
  - id: openai_auth
    type: api_key
    api_key: ${OPENAI_API_KEY}
  
  - id: anthropic_auth
    type: api_key
    api_key: ${ANTHROPIC_API_KEY}
    host: https://api.anthropic.com

models:
  - id: gpt_model
    provider: openai
    auth: openai_auth
  
  - id: claude_model
    provider: anthropic
    auth: anthropic_auth

flows:
  - id: multi_model_flow
    steps:
      - id: openai_step
        model: gpt_model
        inputs:
          - id: prompt
            type: text
        outputs:
          - id: openai_response
            type: text
      
      - id: anthropic_step
        model: claude_model
        inputs:
          - id: prompt
            type: text
        outputs:
          - id: anthropic_response
            type: text
```

### OAuth2 Authentication

```yaml
auths:
  - id: google_oauth
    type: oauth2
    client_id: ${GOOGLE_CLIENT_ID}
    client_secret: ${GOOGLE_CLIENT_SECRET}
    token_url: https://oauth2.googleapis.com/token
    scopes:
      - https://www.googleapis.com/auth/cloud-platform
      - https://www.googleapis.com/auth/bigquery

tools:
  - id: google_api_tool
    name: google_search
    description: "Search using Google Custom Search API"
    endpoint: https://customsearch.googleapis.com/customsearch/v1
    method: GET
    auth: google_oauth
```

### Embedded Authentication

```yaml
flows:
  - id: external_api_flow
    steps:
      - id: api_call
        name: weather_api
        description: "Get weather data"
        endpoint: https://api.weather.com/v1/current
        method: GET
        auth:
          id: weather_auth
          type: api_key
          api_key: ${WEATHER_API_KEY}
          host: https://api.weather.com
        inputs:
          - id: location
            type: text
        outputs:
          - id: weather_data
            type: text
```

### Multiple Service Integration

```yaml
auths:
  - id: aws_auth
    type: api_key
    api_key: ${AWS_ACCESS_KEY_ID}
    client_secret: ${AWS_SECRET_ACCESS_KEY}
    host: https://bedrock-runtime.us-east-1.amazonaws.com
  
  - id: pinecone_auth
    type: api_key
    api_key: ${PINECONE_API_KEY}
    host: https://your-index.svc.us-east1-gcp.pinecone.io

models:
  - id: bedrock_model
    provider: aws-bedrock
    model_id: amazon.nova-lite-v1:0
    auth: aws_auth

indexes:
  - id: vector_store
    name: document-embeddings
    embedding_model: text_embeddings
    auth: pinecone_auth
    args:
      dimension: 1536
      metric: cosine

flows:
  - id: rag_pipeline
    steps:
      - id: search_documents
        index: vector_store
        inputs:
          - id: query
            type: text
        outputs:
          - id: relevant_docs
            type: text
      
      - id: generate_answer
        model: bedrock_model
        system_message: "Answer the question based on the provided documents."
        inputs:
          - id: question
            type: text
          - id: context
            type: text
        outputs:
          - id: answer
            type: text
```

### Environment-Specific Configuration

```yaml
auths:
  - id: dev_auth
    type: api_key
    api_key: ${DEV_API_KEY}
    host: https://dev-api.example.com
  
  - id: prod_auth
    type: oauth2
    client_id: ${PROD_CLIENT_ID}
    client_secret: ${PROD_CLIENT_SECRET}
    token_url: https://api.example.com/oauth/token
    host: https://api.example.com
    scopes:
      - read
      - write

# Use different auth based on environment
models:
  - id: api_model
    provider: custom
    auth: ${AUTH_PROVIDER}  # Set to "dev_auth" or "prod_auth" via environment
```
