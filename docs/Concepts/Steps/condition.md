# Condition

Condition is a step that provides conditional branching logic within flows. It evaluates input values against specified conditions and routes execution to different steps based on the results, enabling dynamic workflow paths and decision-making capabilities.

Condition steps allow flows to adapt their behavior based on runtime data, user inputs, or processing results, making applications more intelligent and responsive to different scenarios.

## Rules and Behaviors

- **Required Input**: Condition steps must have exactly one input variable that provides the value to evaluate.
- **Required Then Step**: The `then` field is mandatory and specifies which step to execute when the condition is true.
- **Optional Else Step**: The `else` field specifies an alternative step to execute when the condition is false.
- **Equality Comparison**: Currently supports equality comparison through the `equals` field.
- **Step References**: Both `then` and `else` can reference steps by ID string or embed step definitions inline.
- **No Direct Outputs**: Condition steps don't produce direct outputs - their behavior determines which subsequent step executes.

--8<-- "components/Condition.md"

## Example Usage

### Basic Conditional Logic

```yaml
flows:
  - id: content_moderation
    steps:
      - id: safety_check
        model: moderation_model
        system_message: "Evaluate content safety. Respond with 'safe' or 'unsafe'."
        inputs:
          - id: content
            type: text
        outputs:
          - id: safety_result
            type: text
      
      - id: handle_moderation
        inputs:
          - id: moderation_result
            type: text
        equals:
          id: safe_content
          type: text
        then:
          id: approve_content
          template: "Content approved: {approved_text}"
          inputs:
            - id: approved_text
              type: text
          outputs:
            - id: approval_message
              type: text
        else:
          id: reject_content
          template: "Content rejected due to safety concerns."
          outputs:
            - id: rejection_message
              type: text
```

### Multi-Path Decision Making

```yaml
flows:
  - id: request_router
    steps:
      - id: classify_request
        model: classifier_model
        system_message: "Classify the request type: 'search', 'generate', or 'analyze'"
        inputs:
          - id: user_request
            type: text
        outputs:
          - id: request_type
            type: text
      
      - id: route_search
        inputs:
          - id: classification
            type: text
        equals:
          id: search_type
          type: text
        then:
          id: perform_search
          index: knowledge_base
          inputs:
            - id: search_query
              type: text
          outputs:
            - id: search_results
              type: text
        else:
          id: check_generation
          inputs:
            - id: classification
              type: text
          equals:
            id: generate_type
            type: text
          then:
            id: generate_content
            model: generation_model
            inputs:
              - id: generation_prompt
                type: text
            outputs:
              - id: generated_content
                type: text
          else:
            id: analyze_content
            model: analysis_model
            system_message: "Perform detailed analysis of the provided content."
            inputs:
              - id: content_to_analyze
                type: text
            outputs:
              - id: analysis_result
                type: text
```

### Error Handling with Conditions

```yaml
flows:
  - id: robust_processing
    steps:
      - id: attempt_processing
        model: processing_model
        inputs:
          - id: input_data
            type: text
        outputs:
          - id: processing_result
            type: text
      
      - id: validate_result
        module_path: "validators"
        function_name: "validate_output"
        inputs:
          - id: result_to_validate
            type: text
        outputs:
          - id: validation_status
            type: text
      
      - id: handle_validation
        inputs:
          - id: validation_outcome
            type: text
        equals:
          id: valid_status
          type: text
        then:
          id: success_handler
          template: "Processing completed successfully: {result}"
          inputs:
            - id: result
              type: text
          outputs:
            - id: success_message
              type: text
        else:
          id: retry_processing
          model: fallback_model
          system_message: "Previous processing failed. Try an alternative approach."
          inputs:
            - id: original_input
              type: text
          outputs:
            - id: retry_result
              type: text
```

### User Permission Checking

```yaml
flows:
  - id: permission_based_access
    steps:
      - id: check_permissions
        module_path: "auth_utils"
        function_name: "check_user_permissions"
        inputs:
          - id: user_id
            type: text
          - id: requested_action
            type: text
        outputs:
          - id: permission_result
            type: text
      
      - id: authorize_action
        inputs:
          - id: permission_check
            type: text
        equals:
          id: authorized_status
          type: text
        then:
          id: execute_privileged_action
          model: admin_model
          system_message: "You have admin privileges. Proceed with the requested action."
          inputs:
            - id: admin_request
              type: text
          outputs:
            - id: admin_result
              type: text
        else:
          id: deny_access
          template: "Access denied. You don't have permission to perform: {action}"
          inputs:
            - id: action
              type: text
          outputs:
            - id: denial_message
              type: text
```

### Dynamic Model Selection

```yaml
models:
  - id: fast_model
    provider: openai
    model_id: gpt-3.5-turbo
  
  - id: smart_model
    provider: openai
    model_id: gpt-4o

flows:
  - id: adaptive_processing
    steps:
      - id: assess_complexity
        module_path: "complexity_analyzer"
        function_name: "analyze_request_complexity"
        inputs:
          - id: user_request
            type: text
        outputs:
          - id: complexity_score
            type: text
      
      - id: select_model
        inputs:
          - id: complexity
            type: text
        equals:
          id: high_complexity
          type: text
        then:
          id: use_smart_model
          model: smart_model
          system_message: "This is a complex request requiring careful analysis."
          inputs:
            - id: complex_request
              type: text
          outputs:
            - id: detailed_response
              type: text
        else:
          id: use_fast_model
          model: fast_model
          system_message: "Provide a quick and efficient response."
          inputs:
            - id: simple_request
              type: text
          outputs:
            - id: quick_response
              type: text
```

### Workflow State Management

```yaml
flows:
  - id: stateful_workflow
    steps:
      - id: check_workflow_state
        module_path: "state_manager"
        function_name: "get_current_state"
        inputs:
          - id: workflow_id
            type: text
        outputs:
          - id: current_state
            type: text
      
      - id: handle_state
        inputs:
          - id: state
            type: text
        equals:
          id: initialized_state
          type: text
        then:
          id: begin_processing
          model: processing_model
          inputs:
            - id: initial_data
              type: text
          outputs:
            - id: processing_result
              type: text
        else:
          id: check_in_progress
          inputs:
            - id: state
              type: text
          equals:
            id: in_progress_state
            type: text
          then:
            id: continue_processing
            model: processing_model
            system_message: "Continue from where we left off."
            inputs:
              - id: partial_data
                type: text
            outputs:
              - id: continued_result
                type: text
          else:
            id: finalize_workflow
            template: "Workflow completed with final state: {final_state}"
            inputs:
              - id: final_state
                type: text
            outputs:
              - id: completion_message
                type: text
```
