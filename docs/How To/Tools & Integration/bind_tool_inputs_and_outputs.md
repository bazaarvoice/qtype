# Bind Tool Inputs and Outputs

Map flow variables to tool parameters and capture tool results using `input_bindings` and `output_bindings` in the InvokeTool step.

### QType YAML

```yaml
steps:
  # Tool with no inputs, only output binding
  - type: InvokeTool
    id: get_current_time
    tool: qtype.application.commons.tools.get_current_timestamp
    input_bindings: {}
    output_bindings:
      result: current_time
    outputs: [current_time]

  # Tool with multiple input bindings
  - type: InvokeTool
    id: add_days
    tool: qtype.application.commons.tools.timedelta
    input_bindings:
      timestamp: current_time      # Tool param ← flow variable
      days: days_until_due          # Tool param ← flow variable
    output_bindings:
      result: deadline_time         # Tool output → flow variable
    outputs: [deadline_time]
```

### Explanation

- **input_bindings**: Maps tool parameter names (left) to flow variable names (right)
- **output_bindings**: Maps tool output names (left) to flow variable names (right)
- **outputs**: Lists flow variables this step produces (must match output_bindings values)
- **Chaining**: Output variables from one tool become input variables for the next tool

## Complete Example

```yaml
--8<-- "../examples/tutorials/04_tools_and_function_calling.qtype.yaml"
```

## See Also

- [Tutorial: Tools and Function Calling](../../Tutorials/04-tools-and-function-calling.md)
- [InvokeTool Reference](../../components/InvokeTool.md)
- [Create Tools from Python Modules](create_tools_from_python_modules.md)
