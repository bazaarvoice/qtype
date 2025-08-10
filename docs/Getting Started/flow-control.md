# Flow Control and Variables

QType flows orchestrate multi-step processing by connecting steps through shared variables. Understanding how variables flow between steps is essential for building effective AI workflows.

## Understanding Flows

--8<-- "components/Flow.md"

A **Flow** executes steps in sequence, automatically passing data between them through variables. The key concept is **variable binding** - how step outputs become inputs for subsequent steps.

```yaml
flows:
  - id: simple_flow
    steps:
      - id: step1
        outputs:
          - id: shared_data
            type: text
      - id: step2
        inputs:
          - shared_data  # Automatically receives output from step1
```

## Variable Flow Between Steps

Variables are the primary way data moves between steps. When a step produces an output variable, any subsequent step can use it as input by referencing its ID.

### Basic Variable Passing

```yaml
flows:
  - id: data_pipeline
    steps:
      # Step 1: Create some data
      - id: create_data
        template: "User input: {{user_question}}"
        inputs:
          - id: user_question
            type: text
        outputs:
          - id: formatted_input  # This variable is now available
            type: text
            
      # Step 2: Process the data
      - id: process_data
        model: gpt-4
        system_message: "Process this input thoughtfully."
        inputs:
          - formatted_input  # References output from step1
        outputs:
          - id: ai_response
            type: text
            
      # Step 3: Format final output
      - id: format_result
        template: "Final result: {{ai_response}}"
        inputs:
          - ai_response  # References output from step2
        outputs:
          - id: final_output
            type: text
```

### Variable Reuse

Variables remain available throughout the flow, so later steps can access outputs from any earlier step:

```yaml
flows:
  - id: reuse_example
    steps:
      - id: step1
        outputs:
          - id: original_data
            type: text
            
      - id: step2
        outputs:
          - id: processed_data
            type: text
            
      - id: step3
        inputs:
          - original_data   # From step1
          - processed_data  # From step2
        template: |
          Original: {{original_data}}
          Processed: {{processed_data}}
```

## Variable Types and Compatibility

Variables have types that must be compatible between steps:

```yaml
flows:
  - id: type_example
    steps:
      - id: text_producer
        outputs:
          - id: text_data
            type: text  # Produces text
            
      - id: text_consumer
        inputs:
          - text_data  # Expects text - compatible!
            
      - id: chat_step
        inputs:
          - id: message_input
            type: ChatMessage  # Different type
        # text_data cannot be used here without conversion
```

### Type Conversion with Templates

Use PromptTemplate steps to convert between types:

```yaml
flows:
  - id: conversion_example
    steps:
      - id: produce_text
        outputs:
          - id: simple_text
            type: text
            
      # Convert text to structured format
      - id: structure_data
        template: |
          {
            "role": "user",
            "blocks": [
              {
                "type": "text",
                "content": "{{simple_text}}"
              }
            ]
          }
        inputs:
          - simple_text
        outputs:
          - id: structured_message
            type: ChatMessage
            
      - id: use_structured
        inputs:
          - structured_message  # Now compatible with ChatMessage
```

## Multi-Step Flow Examples

### Three-Step Processing Chain

```yaml
id: processing_chain
flows:
  - id: analyze_and_respond
    steps:
      # Step 1: Prepare the input
      - id: prepare_input
        template: |
          Analyze this user question: {{raw_question}}
        inputs:
          - id: raw_question
            type: text
        outputs:
          - id: prepared_prompt
            type: text
            
      # Step 2: Get AI analysis
      - id: analyze
        model: gpt-4
        system_message: "Provide detailed analysis."
        inputs:
          - prepared_prompt
        outputs:
          - id: analysis_result
            type: text
            
      # Step 3: Format the final response
      - id: format_response
        template: |
          ## Analysis Results
          
          {{analysis_result}}
          
          *Generated in response to: {{raw_question}}*
        inputs:
          - analysis_result
          - raw_question  # Reusing from step 1
        outputs:
          - id: final_response
            type: text
```

## Common Variable Patterns

### Variable Naming Conventions

Use clear, descriptive names that indicate the data's purpose and lifecycle:

```yaml
# ✅ Good variable names
flows:
  - id: clear_naming
    steps:
      - id: extract_entities
        outputs:
          - id: extracted_entities  # Clear what it contains
            type: array
            
      - id: validate_entities
        inputs:
          - extracted_entities
        outputs:
          - id: validated_entities  # Clear transformation
            type: array
            
      - id: format_final_output
        inputs:
          - validated_entities
        outputs:
          - id: formatted_entity_report  # Clear final purpose
            type: text
```

### Multiple Input Variables

Steps can use multiple variables from different earlier steps:

```yaml
flows:
  - id: multi_input_example
    steps:
      - id: get_user_data
        outputs:
          - id: user_info
            type: text
            
      - id: get_preferences
        outputs:
          - id: user_preferences
            type: text
            
      - id: personalize_response
        template: |
          Based on your info: {{user_info}}
          And your preferences: {{user_preferences}}
          Here's a personalized response...
        inputs:
          - user_info       # From step 1
          - user_preferences # From step 2
        outputs:
          - id: personalized_message
            type: text
```

### Variable Scope and Lifecycle

Variables are available from when they're created until the flow ends:

```yaml
flows:
  - id: variable_lifecycle
    steps:
      - id: early_step
        outputs:
          - id: early_data
            type: text
            # early_data is now available to all following steps
            
      - id: middle_step
        inputs:
          - early_data  # Can use early_data
        outputs:
          - id: middle_data
            type: text
            # middle_data is now also available
            
      - id: late_step
        inputs:
          - early_data   # Still available
          - middle_data  # Also available
        # Can use variables from any earlier step
```

### Debugging Tips

1. **Check variable names carefully** - Case-sensitive and must match exactly
2. **Verify step order** - Variables must be created before they're used
3. **Confirm types match** - Use conversion steps when needed
4. **Use descriptive names** - Easier to track data flow

Understanding variable flow between steps is the key to building effective QType applications. Focus on clear variable names, proper ordering, and type compatibility to create reliable multi-step workflows.
