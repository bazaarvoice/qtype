# Include QType YAML

Organize QType applications into reusable modules by including external YAML files using the `!include` directive, allowing you to share models, tools, authentication providers, and other resources across multiple applications.

### QType YAML

```yaml
id: my_app

# Include shared resources from other files
references:
  - !include common/auth.qtype.yaml
  - !include common/models.qtype.yaml
  - !include common/tools.qtype.yaml

flows:
  - id: main_flow
    steps:
      - type: LLMInference
        id: generate
        model: shared_gpt4        # References model from included file
        prompt: "Generate a summary"
```

**common/models.qtype.yaml:**
```yaml
- id: shared_gpt4
  type: Model
  provider: openai
  model_id: gpt-4
  auth: shared_openai_auth
```

### Explanation

- **!include**: YAML tag that loads and parses external YAML files, merging their content into the current specification
- **Relative paths**: File paths are resolved relative to the including YAML file's location
- **Nested includes**: Included files can include other files, creating a hierarchy of modular components
- **Remote includes**: Supports URLs (e.g., `!include https://example.com/config.yaml`) via fsspec

## See Also

- [Reference Entities by ID](reference_entities_by_id.md)
- [Include Raw Text from Other Files](include_raw_text_from_other_files.md)
- [Application Reference](../../components/Application.md)
