# LLMInference

LLMInference is a step that performs direct language model inference, sending prompts to AI models and capturing their responses. It provides the core interface for integrating large language models into QType workflows, supporting both simple text generation and complex conversational interactions.

LLMInference steps can maintain conversation context through memory, apply system prompts for role-setting, and handle various input formats to create flexible AI-powered applications.

## Rules and Behaviors

- **Required Model**: The `model` field is mandatory and specifies which model configuration to use for inference.
- **Automatic Output**: If no outputs are specified, automatically creates a single output variable named `{step_id}.response` of type `text`.
- **Memory Integration**: Can optionally reference a Memory object to maintain conversation history and context across multiple interactions.
- **System Message**: Optional `system_message` field sets the AI's role and behavior context.
- **Flexible Inputs**: Can accept any number of input variables that will be passed to the model.
- **Model Reference**: Can reference models by ID string or embed model configuration inline.

--8<-- "components/LLMInference.md"

## Related Concepts

LLMInference steps require [Model](../Concepts/model.md) configurations, may use [Memory](../Concepts/memory.md) for context retention, often consume output from [PromptTemplate](prompt-template.md) steps, and are extended by [Agent](agent.md) steps for tool-enabled interactions.

## Example Usage

### Basic Text Generation

```yaml
id: text_generation_app

models:
  - id: gpt_model
    provider: openai
    model_id: gpt-4o
    auth: openai_auth

flows:
  - id: simple_generation
    steps:
      - id: generate_text
        model: gpt_model
        system_message: "You are a helpful writing assistant."
        inputs:
          - id: prompt
            type: text
        outputs:
          - id: generated_content
            type: text
```

### Conversational AI with Memory

```yaml
memories:
  - id: chat_memory
    token_limit: 50000
    chat_history_token_ratio: 0.8

models:
  - id: chat_model
    provider: openai
    model_id: gpt-4o
    inference_params:
      temperature: 0.7
      max_tokens: 1000

flows:
  - id: conversation_flow
    steps:
      - id: chat_response
        model: chat_model
        memory: chat_memory
        system_message: |
          You are a knowledgeable assistant that remembers our conversation 
          history and provides helpful, contextual responses.
        inputs:
          - id: user_message
            type: text
        outputs:
          - id: assistant_response
            type: text
```

### Multi-Step Analysis Pipeline

```yaml
flows:
  - id: document_analysis
    steps:
      - id: extract_summary
        model: gpt_model
        system_message: "Extract a concise summary from the provided text."
        inputs:
          - id: document_text
            type: text
        outputs:
          - id: document_summary
            type: text
      
      - id: identify_themes
        model: gpt_model
        system_message: "Identify the main themes and topics in this summary."
        inputs:
          - id: summary_text
            type: text
        outputs:
          - id: main_themes
            type: text
      
      - id: generate_recommendations
        model: gpt_model
        system_message: |
          Based on the themes identified, provide actionable recommendations.
        inputs:
          - id: themes
            type: text
        outputs:
          - id: recommendations
            type: text
```

### Embedded Model Configuration

```yaml
flows:
  - id: inline_model_flow
    steps:
      - id: custom_analysis
        model:
          id: specialized_model
          provider: anthropic
          model_id: claude-3-opus
          auth:
            id: anthropic_auth
            type: api_key
            api_key: ${ANTHROPIC_API_KEY}
          inference_params:
            temperature: 0.3
            max_tokens: 2000
        system_message: "You are an expert analyst specializing in technical documentation."
        inputs:
          - id: technical_document
            type: text
        outputs:
          - id: technical_analysis
            type: text
```

### Prompt Template Integration

```yaml
flows:
  - id: structured_prompt_flow
    steps:
      - id: build_analysis_prompt
        template: |
          Analyze the following {content_type}:
          
          Title: {title}
          Content: {content}
          
          Please provide:
          1. Key insights
          2. Strengths and weaknesses
          3. Recommendations
        inputs:
          - id: content_type
            type: text
          - id: title
            type: text
          - id: content
            type: text
        outputs:
          - id: structured_prompt
            type: text
      
      - id: perform_analysis
        model: analysis_model
        system_message: "You are a thorough analyst with expertise across multiple domains."
        inputs:
          - id: prompt
            type: text
        outputs:
          - id: comprehensive_analysis
            type: text
```

### Multi-Model Comparison

```yaml
models:
  - id: model_a
    provider: openai
    model_id: gpt-4o
  
  - id: model_b
    provider: anthropic
    model_id: claude-3-opus

flows:
  - id: model_comparison
    steps:
      - id: analysis_with_model_a
        model: model_a
        system_message: "Provide a detailed analysis of the given topic."
        inputs:
          - id: topic
            type: text
        outputs:
          - id: analysis_a
            type: text
      
      - id: analysis_with_model_b
        model: model_b
        system_message: "Provide a detailed analysis of the given topic."
        inputs:
          - id: topic
            type: text
        outputs:
          - id: analysis_b
            type: text
      
      - id: synthesize_analyses
        model: model_a
        system_message: |
          Compare and synthesize these two analyses to provide 
          a comprehensive perspective.
        inputs:
          - id: first_analysis
            type: text
          - id: second_analysis
            type: text
        outputs:
          - id: synthesized_analysis
            type: text
```

### Automatic Output Example

```yaml
flows:
  - id: auto_output_example
    steps:
      - id: simple_inference
        # No outputs defined - will automatically create "simple_inference.response"
        model: gpt_model
        system_message: "You are a helpful assistant."
        inputs:
          - id: user_question
            type: text
      
      - id: follow_up
        model: gpt_model
        system_message: "Provide a follow-up question based on the previous response."
        inputs:
          - id: previous_response
            type: text
        outputs:
          - id: follow_up_question
            type: text
```
