# Use Environment Variables

Keep sensitive credentials and environment-specific configuration out of your YAML files by using environment variable substitution with `${VAR_NAME}` syntax.

### QType YAML

```yaml
auths:
  - type: api_key
    id: openai_auth
    api_key: ${OPENAI_KEY}        # Required variable
    host: https://api.openai.com

models:
  - type: Model
    id: gpt4
    provider: openai
    model_id: ${MODEL_NAME:-gpt-4}  # Optional with default
    auth: openai_auth
```

### Explanation

- **`${VAR_NAME}`**: Substitutes the value of environment variable `VAR_NAME`; raises error if not set
- **`${VAR_NAME:-default}`**: Substitutes the value of `VAR_NAME` or uses `default` if not set
- **Environment variable resolution**: Happens during YAML loading, before validation and execution
- **Works everywhere**: Can be used in any string value throughout the YAML specification

## Setting Environment Variables

```bash
# Export before running
export OPENAI_KEY="sk-..."
qtype run app.qtype.yaml

# Or set inline
OPENAI_KEY="sk-..." uv run qtype run app.qtype.yaml

# Or in a .env file (automatically loaded via the loader)
echo 'OPENAI_KEY="sk-..."' >> .env
qtype run app.qtype.yaml
```

## See Also

- [Tutorial: Your First QType Application](../../Tutorials/01-first-qtype-application.md)
- [APIKeyAuthProvider Reference](../../components/APIKeyAuthProvider.md)
