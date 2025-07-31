# Tool

A tool represents an external capability that can be invoked to perform specific tasks, integrate with external services, or execute custom functions. Tools provide the bridge between QType applications and the outside world, enabling workflows to interact with APIs, databases, file systems, and custom business logic.

Tools can be used directly as [Steps](Steps/index.md) or made available to [Agents](Steps/agent.md) for autonomous decision-making. They abstract away the complexity of external integrations while providing a consistent interface for authentication, error handling, and data flow.

## Rules and Behaviors

- **Dual Usage**: Tools can be used as standalone steps in flows or provided to agents for autonomous invocation
- **Authentication Support**: Tools can reference [AuthorizationProvider](authorization-provider.md) objects for secure access to external resources
- **Input/Output Variables**: Tools define their interface through inputs and outputs, enabling data flow between components
- **Error Handling**: Tools provide structured error handling for network issues, authentication failures, and execution errors
- **Type Safety**: Tool inputs and outputs are validated against their declared variable types
- **Execution Context**: Tools execute within the QType runtime environment with access to variables and configuration
- **Reusability**: Tools can be defined once and used across multiple flows or made available to different agents

## Tool Types

--8<-- "components/APITool.md"

--8<-- "components/PythonFunctionTool.md"

## Related Concepts

Tools integrate with [AuthorizationProvider](authorization-provider.md) for secure access, can be used as [Steps](Steps/index.md) in [Flows](flow.md), and are essential for [Agent](Steps/agent.md) capabilities. They consume and produce [Variables](variable.md) for data flow and may interact with [Models](model.md) and [Indexes](index-concept.md).

