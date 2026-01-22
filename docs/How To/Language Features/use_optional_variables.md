# Use Optional Variables

Mark variables as optional to handle cases where data may be missing or unset, allowing your flow to continue gracefully instead of failing.

### QType YAML

```yaml
variables:
  - id: email
    type: text?           # Optional text variable
```

### Explanation

- **`?` suffix**: Shorthand syntax to mark a variable as optional
- **Optional variables**: Can be `None` or set to a value
- **FieldExtractor**: Returns `None` for optional output variables when JSONPath finds no matches, instead of raising an error. If you make the variable non-optional, it will raise an error.

## Complete Example

```yaml
--8<-- "../examples/language_features/optional_variables.qtype.yaml"
```

**Run it:**
```bash
# When email field exists
qtype run examples/language_features/optional_variables.qtype.yaml -i '{"user_profile": {"email":"hello@domain.com"}}'
# Results:                                                                                          
# email: hello@domain.com

# When email field is missing
qtype run examples/language_features/optional_variables.qtype.yaml -i '{"user_profile": "just text"}'
# Results:                                                                                          
# email: None  
```

## See Also

- [Variable Reference](../../components/Variable.md)
- [FieldExtractor Reference](../../components/FieldExtractor.md)
