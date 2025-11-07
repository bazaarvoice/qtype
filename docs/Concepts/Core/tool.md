# Tool

A tool represents an external capability that can be invoked to perform specific tasks, integrate with external services, or execute custom functions. Tools provide the bridge between QType applications and the outside world, enabling workflows to interact with APIs, databases, file systems, and custom business logic.

Tools are defined at the application level and can be:
- Invoked directly using the InvokeTool step
- Made available to [Agents](../Steps/agent.md) for autonomous decision-making

## Key Principles

### Type Discriminator

All tools must include a `type` field for proper schema validation:
- `type: PythonFunctionTool` for Python function calls
- `type: APITool` for HTTP API endpoints

### Centralized Definition

Tools are defined once at the application level and referenced by ID:

```yaml
tools:
  - type: PythonFunctionTool
    id: my_calculator
    name: calculate
    description: Performs calculations
    function_name: calculate
    module_path: my_tools.calculator
    inputs:
      expression:
        type: text
        optional: false
    outputs:
      result:
        type: text
        optional: false

flows:
  - type: Flow
    id: my_flow
    steps:
      - type: InvokeTool
        tool: my_calculator  # References by ID
```

## Rules and Behaviors

- **Dual Usage**: Tools can be used as standalone steps (via InvokeTool) or provided to agents for autonomous invocation
- **Authentication Support**: Tools can reference [AuthorizationProvider](authorization-provider.md) by ID for secure access to external resources
- **Input/Output Parameters**: Tools define their interface through input and output parameter dictionaries
- **Type Safety**: Tool parameters are validated against their declared types
- **Reusability**: Tools defined once can be used across multiple flows or agents

## Tool Types

--8<-- "components/APITool.md"

--8<-- "components/PythonFunctionTool.md"

## Related Concepts

Tools integrate with [AuthorizationProvider](authorization-provider.md) for secure access, can be used as [Steps](../Steps/index.md) in [Flows](flow.md), and are essential for [Agent](../Steps/agent.md) capabilities. They consume and produce [Variables](variable.md) for data flow and may interact with [Models](model.md) and [Indexes](indexes.md).

