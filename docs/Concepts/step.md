# Step

A step represents any executable component that can take inputs and produce outputs within a QType application. Steps are the fundamental building blocks of workflows, providing a consistent interface for operations ranging from simple prompt templates to complex AI agent interactions.

All steps share common properties (ID, inputs, outputs) while implementing specific behaviors for their domain. Steps can be composed into [Flows](flow.md) to create sophisticated pipelines, and they can reference each other to build modular, reusable applications.

## Rules and Behaviors

- **Unique IDs**: Each step must have a unique `id` within the application. Duplicate step IDs will result in a validation error.
- **Abstract Base Class**: Step is an abstract base class - you must use concrete implementations for actual functionality.
- **Input/Output Variables**: Steps define their interface through optional `inputs` and `outputs` lists that specify the data they consume and produce.
- **Variable References**: Input and output variables can be specified as Variable objects or as string references to variables defined elsewhere.
- **Optional Interface**: Both `inputs` and `outputs` are optional - some steps may infer them automatically or have default behaviors.
- **Flow Integration**: All steps can be included in flows and can be referenced by other steps.
- **Polymorphic Usage**: Steps can be used polymorphically - any step type can be used wherever a Step is expected.

## Base Step Type

--8<-- "components/Step.md"

## Step Types

QType provides several categories of steps for different use cases:

### AI and Language Model Steps
- **[LLMInference](../Steps/llm-inference.md)** - Direct language model inference with prompts
- **[Agent](../Steps/agent.md)** - AI agents with tool access and decision-making capabilities
- **[PromptTemplate](../Steps/prompt-template.md)** - Dynamic prompt generation with variable substitution

### Tool and Integration Steps
- **[Tool](tool.md)** - External integrations and function execution (Tools can also be used as steps)

### Search and Retrieval Steps
- **[Search Steps](../Steps/search.md)** - Vector similarity search and document search operations

### Control Flow and Processing Steps
- **[Flow](../Steps/flow.md)** - Orchestration of multiple steps (see [Flow concept](flow.md) for detailed information)
- **[Condition](../Steps/condition.md)** - Conditional branching logic
- **[Decoder](../Steps/decoder.md)** - Structured data parsing and extraction

## Related Concepts

Steps are orchestrated by [Flows](flow.md), may reference [Models](model.md) for AI operations, can use [Tools](tool.md) for external integrations, and access [Indexes](index-concept.md) for search operations. They also define and consume [Variables](variable.md) for data flow.

## Example Usage

### Basic Step Composition

```yaml
id: content_pipeline

flows:
  - id: process_content
    steps:
      - id: generate_prompt
        template: "Analyze this content: {content}"
        inputs:
          - id: content
            type: text
        outputs:
          - id: analysis_prompt
            type: text
      
      - id: analyze_content
        model: gpt-4o
        inputs:
          - id: prompt
            type: text
        outputs:
          - id: analysis
            type: text
      
      - id: extract_insights
        format: json
        inputs:
          - id: raw_analysis
            type: text
        outputs:
          - id: structured_insights
            type: text
```

### Polymorphic Step Usage

```yaml
flows:
  - id: flexible_workflow
    steps:
      # Different step types used polymorphically
      - id: data_source
        # Could be APITool, PythonFunctionTool, etc.
        endpoint: "https://api.example.com/data"
        method: GET
        outputs:
          - id: raw_data
            type: text
      
      - id: processor
        # Could be LLMInference, Agent, etc.
        model: processing_model
        inputs:
          - id: data_to_process
            type: text
        outputs:
          - id: processed_data
            type: text
      
      - id: conditional_logic
        inputs:
          - id: decision_input
            type: text
        equals:
          id: success_condition
          type: text
        then:
          id: success_handler
          template: "Success: {result}"
        else:
          id: error_handler
          template: "Error: {error}"
```

### Step Reference Patterns

```yaml
# Define reusable steps
flows:
  - id: preprocessing_flow
    steps:
      - id: clean_data
        module_path: "data_utils"
        function_name: "clean_text"
        inputs:
          - id: raw_text
            type: text
        outputs:
          - id: cleaned_text
            type: text
      
      - id: validate_data
        module_path: "data_utils" 
        function_name: "validate_format"
        inputs:
          - id: text_to_validate
            type: text
        outputs:
          - id: validation_result
            type: text

# Reference steps in multiple contexts
flows:
  - id: main_workflow
    steps:
      - id: preprocess_input
        # Reference to preprocessing flow
        flow: preprocessing_flow
        inputs:
          - id: user_input
            type: text
      
      - id: main_processing
        model: main_model
        inputs:
          - id: processed_input
            type: text
        outputs:
          - id: result
            type: text
```

### Advanced Step Orchestration

```yaml
memories:
  - id: conversation_memory

flows:
  - id: intelligent_assistant
    steps:
      - id: understand_intent
        model: intent_model
        system_message: "Determine the user's intent and extract key information."
        inputs:
          - id: user_message
            type: text
        outputs:
          - id: intent_analysis
            type: text
      
      - id: route_request
        inputs:
          - id: intent
            type: text
        equals:
          id: search_intent
          type: text
        then:
          id: search_step
          index: knowledge_base
          inputs:
            - id: search_query
              type: text
          outputs:
            - id: search_results
              type: text
        else:
          id: direct_response
          model: response_model
          memory: conversation_memory
          inputs:
            - id: query
              type: text
          outputs:
            - id: direct_answer
              type: text
      
      - id: generate_final_response
        model: synthesis_model
        memory: conversation_memory
        system_message: "Synthesize the information to provide a helpful response."
        inputs:
          - id: user_request
            type: text
          - id: information
            type: text
        outputs:
          - id: final_response
            type: text
```
