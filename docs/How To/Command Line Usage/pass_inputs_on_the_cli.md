# Pass Inputs On The CLI

Provide input values to your QType flows directly from the command line using JSON-formatted input data, enabling dynamic parameterization of applications without modifying YAML files.

### CLI Usage

```bash
# Pass a single input variable
qtype run -i '{"user_name":"Alice"}' app.qtype.yaml

# Pass multiple input variables
qtype run -i '{"model_id":"claude-3", "temperature":0.7}' app.qtype.yaml

# Pass complex nested structures
qtype run -i '{"config":{"max_tokens":1000,"top_p":0.9}}' app.qtype.yaml

# Specify which flow to run with inputs
qtype run -f analyze_data -i '{"threshold":0.85}' app.qtype.yaml
```

### Explanation

- **`-i`, `--input`**: Accepts a JSON blob containing key-value pairs where keys match variable names declared in your flow's `inputs` field
- **JSON format**: Must be valid JSON with double quotes for strings, properly escaped special characters
- **Flow inputs**: The variables must match those declared in the flow's `inputs` list or the application's `inputs` list
- **`-f`, `--flow`**: Specifies which flow to run when your application contains multiple flows (defaults to first flow if omitted)

## Complete Example

The [LLM Processing Pipelines](../../Gallery/dataflow_pipelines.md) example demonstrates passing the output file path as a CLI input:

```bash
# Run the pipeline with a custom output path
qtype run -i '{"output_path":"results.parquet"}' \
  --progress \
  examples/data_processing/dataflow_pipelines.qtype.yaml
```

The flow declares `output_path` in its inputs:

```yaml
flows:
  - name: analyze_reviews
    inputs:
      - output_path  # Receives value from CLI -i flag
```

## See Also

- [Load Multiple Inputs from Files](load_multiple_inputs_from_files.md)
- [CLI Reference](../../Reference/cli.md)
- [Gallery: Dataflow Pipelines](../../Gallery/dataflow_pipelines.md)
