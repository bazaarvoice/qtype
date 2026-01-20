# Reuse Prompts with Templates

Define reusable prompt templates with variable placeholders using the `PromptTemplate` step, enabling consistent prompt formatting and dynamic content substitution.

### QType YAML

```yaml
steps:
  - id: create_prompt
    type: PromptTemplate
    template: |
      Analyze this product review in 1-2 sentences. Include:
      - Overall sentiment (positive/negative/mixed)
      - Key themes or points

      Product: {product_name}
      Rating: {rating}/5
      Review: {review_text}
    inputs:
      - product_name
      - rating
      - review_text
    outputs:
      - analysis_prompt
```

### Explanation

- **type: PromptTemplate**: Step that formats strings with variable placeholders using Python's `str.format()` syntax
- **template**: String with `{variable_name}` placeholders that get replaced with actual values from inputs
- **inputs**: Variables whose values will be substituted into the template placeholders
- **outputs**: Single variable containing the formatted prompt string ready for LLM inference

## See Also

- [PromptTemplate Reference](../../components/PromptTemplate.md)
- [How-To: Include Raw Text from Other Files](../../How%20To/Language%20Features/include_raw_text.md)
- [How-To: Invoke LLMs with System Messages](invoke_llms_with_system_messages.md)
- [Tutorial: Your First QType Application](../../Tutorials/your_first_qtype_application.md)
