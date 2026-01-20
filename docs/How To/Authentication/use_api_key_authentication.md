# Use API Key Authentication

Authenticate with model providers like OpenAI using API keys, either from environment variables or stored in secret managers.

### QType YAML

```yaml
auths:
  - type: api_key
    id: openai_auth
    api_key: ${OPENAI_KEY}
    host: https://api.openai.com

models:
  - type: Model
    id: gpt-4
    provider: openai
    model_id: gpt-4-turbo
    auth: openai_auth
```

### Explanation

- **type: api_key**: Specifies this is an API key-based authentication provider
- **api_key**: The API key value, typically loaded from an environment variable using `${VAR_NAME}` syntax
- **host**: Base URL or domain of the provider (optional, some providers infer this)
- **auth**: Reference to the auth provider by its ID when configuring models

## Complete Example

```yaml
--8<-- "../examples/tutorials/01_hello_world.qtype.yaml"
```

## See Also

- [APIKeyAuthProvider Reference](../../components/APIKeyAuthProvider.md)
- [Use Environment Variables](../Language%20Features/use_environment_variables.md)
- [Model Reference](../../components/Model.md)
- [Tutorial: Your First QType Application](../../Tutorials/your_first_qtype_application.md)
