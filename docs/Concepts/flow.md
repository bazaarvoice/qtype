# Flow

A flow defines a sequence of [Steps](Steps/index.md) that work together to accomplish a specific task or workflow. Flows are the primary orchestration mechanism in QType, allowing you to chain multiple operations such as LLM inference, tool calls, data processing, and conditional logic into coherent, reusable workflows.

Flows themselves are steps, meaning they can be nested within other flows to create complex, hierarchical workflows. This composability allows you to build modular applications where common patterns can be extracted into reusable flow components.

## Rules and Behaviors

- **Unique IDs**: Each flow must have a unique `id` within the application. Duplicate flow IDs will result in a validation error.
- **Required Steps**: Flows must contain at least one step. Empty flows will result in a `FlowHasNoStepsError` validation error.
- **Input Inference**: If `inputs` are not explicitly defined, they are automatically inferred from the inputs of the first step in the flow.
- **Output Inference**: If `outputs` are not explicitly defined, they are automatically inferred from the outputs of the last step in the flow.
- **Step References**: Steps can be referenced by ID (string) or embedded as inline objects within the flow definition.
- **Sequential Execution**: Steps within a flow are executed in the order they appear in the `steps` list.

--8<-- "components/Flow.md"

## Related Concepts

Flows orchestrate [Step](Steps/index.md) components to create workflows. Any step type can be included in a flow, including other flows for nested workflows.
