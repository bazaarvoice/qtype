# Step

A step represents any executable component that can take inputs and produce outputs within a QType application. Steps are the fundamental building blocks of workflows, providing a consistent interface for operations ranging from simple prompt templates to complex AI agent interactions.

All steps share common properties (ID, inputs, outputs) while implementing specific behaviors for their domain. Steps can be composed into [Flows](../Core/flow.md) to create sophisticated pipelines, and they can reference each other to build modular, reusable applications.

## Rules and Behaviors

- **Unique IDs**: Each step must have a unique `id` within the application. Duplicate step IDs will result in a validation error.
- **Abstract Base Class**: Step is an abstract base class - you must use concrete implementations for actual functionality.
- **Input/Output Variables**: Steps define their interface through optional `inputs` and `outputs` lists that specify the data they consume and produce.
- **Variable References**: Input and output variables can be specified as Variable objects or as string references to variables defined elsewhere.
- **Optional Interface**: Both `inputs` and `outputs` are optional - some steps may infer them automatically or have default behaviors.
- **Flow Integration**: All steps can be included in flows and can be referenced by other steps.
- **Polymorphic Usage**: Steps can be used polymorphically - any step type can be used wherever a Step is expected.

## Component Definition

--8<-- "components/Step.md"

## Step Types

QType provides several categories of steps for different use cases:

### AI and Language Model Steps
- **[LLMInference](llm-inference.md)** - Direct language model inference with prompts
- **[Agent](agent.md)** - AI agents with tool access and decision-making capabilities
- **[PromptTemplate](prompt-template.md)** - Dynamic prompt generation with variable substitution

### Tool and Integration Steps
- **[Tool](../Core/tool.md)** - External integrations and function execution (Tools can also be used as steps)

### Search and Retrieval Steps
- **[Search Steps](search.md)** - Vector similarity search and document search operations

### Control Flow and Processing Steps
- **[Flow](../Core/flow.md)** - Orchestration of multiple steps (see [Flow concept](../Core/flow.md) for detailed information)
- **[Decoder](decoder.md)** - Structured data parsing and extraction

## Related Concepts

Steps are orchestrated by [Flows](../Core/flow.md), may reference [Models](../Core/model.md) for AI operations, can use [Tools](../Core/tool.md) for external integrations, and access [Indexes](../Core/indexes.md) for search operations. They also define and consume [Variables](../Core/variable.md) for data flow.
