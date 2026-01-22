# Invoke Other Flows

Reuse flows as composable building blocks by invoking them from other flows with input and output bindings.

### QType YAML

```yaml
flows:
  # Define reusable flow
  - type: Flow
    id: summarize_text
    variables:
      - id: input_text
        type: text
      - id: output_summary
        type: text
    inputs: [input_text]
    outputs: [output_summary]
    steps:
      - type: LLMInference
        id: summarizer
        model: my_model
        inputs: [input_text]
        outputs: [output_summary]

  # Main flow invokes the reusable flow
  - type: Flow
    id: main
    variables:
      - id: article
        type: text
      - id: summary
        type: text
    inputs: [article]
    outputs: [summary]
    steps:
      - type: InvokeFlow
        id: get_summary
        flow: summarize_text           # Reference to flow by ID
        input_bindings:
          input_text: article          # Map flow input to step variable
        output_bindings:
          output_summary: summary      # Map flow output to step variable
```

### Explanation

- **InvokeFlow**: Step type that executes another flow with variable mapping
- **flow**: ID of the flow to invoke (must be defined in the application)
- **input_bindings**: Maps flow input variables to the invoking step's variables (format: `flow_input_name: step_variable_name`)
- **output_bindings**: Maps flow output variables to the invoking step's variables (format: `flow_output_name: step_variable_name`)
- **Reusability**: Flows can be invoked multiple times with different bindings

## Complete Example

```yaml
--8<-- "../examples/data_processing/invoke_other_flows.qtype.yaml"
```

**Run it:**
```bash
qtype run examples/data_processing/invoke_other_flows.qtype.yaml \
  --flow main \
  --input '{"article_text": "Your article text here..."}'
```

## See Also

- [InvokeFlow Reference](../../components/InvokeFlow.md)
- [Flow Reference](../../components/Flow.md)
- [Example: Data Processing Pipeline](../../Gallery/Data%20Processing/dataflow_pipeline.md)
