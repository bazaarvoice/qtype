# Flow

A flow defines a sequence of [Steps](step.md) that work together to accomplish a specific task or workflow. Flows are the primary orchestration mechanism in QType, allowing you to chain multiple operations such as LLM inference, tool calls, data processing, and conditional logic into coherent, reusable workflows.

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

Flows orchestrate [Step](step.md) components to create workflows. Any step type can be included in a flow, including other flows for nested workflows.

## Example Usage

### Basic Sequential Flow

```yaml
id: document_analysis_app

flows:
  - id: analyze_document
    steps:
      - id: extract_text
        # Document processing step
        inputs:
          - id: document
            type: text
        outputs:
          - id: extracted_text
            type: text
      
      - id: summarize_content
        model: gpt-4o
        system_message: "Summarize the following text concisely."
        inputs:
          - id: content
            type: text
        outputs:
          - id: summary
            type: text
      
      - id: extract_keywords
        model: gpt-4o
        system_message: "Extract 5-10 key terms from this text. Return as a JSON array."
        inputs:
          - id: text_to_analyze
            type: text
        outputs:
          - id: keywords
            type: text
```

### Flow with Conditional Logic

```yaml
flows:
  - id: content_moderation
    steps:
      - id: check_content
        model: gpt-4o
        system_message: "Analyze if this content is appropriate. Respond with 'safe' or 'unsafe'."
        inputs:
          - id: user_content
            type: text
        outputs:
          - id: safety_assessment
            type: text
      
      - id: handle_result
        inputs:
          - id: assessment
            type: text
        equals: 
          id: safe_content
          type: text
        then:
          id: approve_content
          inputs:
            - id: content
              type: text
          outputs:
            - id: approved_message
              type: text
        else:
          id: reject_content
          inputs:
            - id: content
              type: text
          outputs:
            - id: rejection_notice
              type: text
```

### Nested Flows

```yaml
flows:
  - id: research_subtask
    steps:
      - id: search_step
        # Vector search step
      - id: analyze_results
        model: gpt-4o
        # Analysis step

  - id: comprehensive_research
    steps:
      - id: initial_research
        # Reference to another flow
        flow: research_subtask
        inputs:
          - id: query
            type: text
      
      - id: follow_up_research
        flow: research_subtask
        inputs:
          - id: refined_query
            type: text
      
      - id: synthesize_findings
        model: gpt-4o
        system_message: "Synthesize these research findings into a comprehensive report."
        inputs:
          - id: research_data
            type: text
        outputs:
          - id: final_report
            type: text
```

### Flow with External Tool Integration

```yaml
flows:
  - id: data_pipeline
    steps:
      - id: fetch_data
        endpoint: "https://api.example.com/data"
        method: GET
        auth: api_auth
        outputs:
          - id: raw_data
            type: text
      
      - id: process_data
        module_path: "data_processors"
        function_name: "clean_and_transform"
        inputs:
          - id: data
            type: text
        outputs:
          - id: processed_data
            type: text
      
      - id: generate_insights
        model: gpt-4o
        system_message: "Analyze this data and provide key insights."
        inputs:
          - id: data_to_analyze
            type: text
        outputs:
          - id: insights
            type: text
```

### Flow with Memory for Multi-Turn Interaction

```yaml
memories:
  - id: conversation_memory

flows:
  - id: interactive_assistant
    steps:
      - id: understand_request
        model: gpt-4o
        memory: conversation_memory
        system_message: "You are a helpful assistant. Understand the user's request and maintain context."
        inputs:
          - id: user_input
            type: text
        outputs:
          - id: understood_request
            type: text
      
      - id: generate_response
        model: gpt-4o
        memory: conversation_memory
        system_message: "Provide a helpful response based on the conversation history."
        inputs:
          - id: request
            type: text
        outputs:
          - id: assistant_response
            type: text
```
