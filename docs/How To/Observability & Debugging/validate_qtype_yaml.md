# Validate QType YAML

Check your QType YAML files for syntax errors, schema violations, reference issues, and semantic problems before running them.

### Command Line

```bash
# Basic validation
qtype validate path/to/app.qtype.yaml

# Validate and print the parsed document
qtype validate path/to/app.qtype.yaml --print
```

### Validation Checks

- **YAML Syntax**: Verifies valid YAML structure and syntax
- **Schema Validation**: Ensures all fields match the QType schema (Pydantic validation)
- **Reference Resolution**: Checks that all ID references (models, steps, variables) exist
- **Duplicate Detection**: Identifies duplicate component IDs
- **Semantic Validation**: Validates flow logic, type compatibility, and business rules

### Options

- **`--print` / `-p`**: Print the validated document with resolved references and defaults applied

### Exit Codes

- **0**: Validation successful
- **1**: Validation failed (error details printed to stderr)

## See Also

- [CLI Reference](../../Reference/cli.md)
- [Semantic Validation Rules](../../Reference/semantic-validation-rules.md)
- [Visualize Application Architecture](visualize_application_architecture.md)
