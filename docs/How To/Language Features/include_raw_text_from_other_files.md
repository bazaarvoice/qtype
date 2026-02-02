# Include Raw Text from Other Files

Load external text files into your YAML configuration using the `!include_raw` directive, useful for keeping prompts, templates, and long text content in separate files.

### QType YAML

```yaml
steps:
  - id: generate_story
    type: PromptTemplate
    template: !include_raw story_prompt.txt
    inputs:
      - theme
      - tone
    outputs:
      - story
```

**story_prompt.txt:**
```txt
--8<-- "../examples/language_features/story_prompt.txt"
```

### Explanation

- **!include_raw**: YAML tag that loads the contents of an external file as a raw string
- **Relative paths**: File paths are resolved relative to the YAML file's location
- **Template substitution**: The loaded text can contain variable placeholders (e.g., `{theme}`, `{tone}`) that are substituted at runtime
- **Use cases**: Prompt templates, system messages, documentation, or any text content you want to manage separately

## Complete Example

```yaml
--8<-- "../examples/language_features/include_raw.qtype.yaml"
```



**Run it:**
```bash
qtype run include_raw.qtype.yaml -i '{"theme":"a robot learning to paint","tone":"inspirational"}'
```

## See Also

- [PromptTemplate Reference](../../components/PromptTemplate.md)
- [Include QType YAML](include_qtype_yaml.md)
- [Reuse Prompts with Templates](../Invoke%20Models/reuse_prompts_with_templates.md)
