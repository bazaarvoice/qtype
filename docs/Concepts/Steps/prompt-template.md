# PromptTemplate

PromptTemplate is a step that generates dynamic prompts by substituting variables into string templates. It enables the creation of reusable prompt patterns that can be customized with different inputs, making it easy to build flexible prompt-driven workflows.

PromptTemplate steps are particularly useful for preprocessing inputs before sending them to language models, creating consistent prompt formats across different use cases, and building modular prompt libraries that can be shared across applications.

## Rules and Behaviors

- **Required Template**: The `template` field is mandatory and contains the string template with variable placeholders.
- **Variable Substitution**: Uses standard string formatting with curly braces `{variable_name}` for variable placeholders.
- **Automatic Output**: If no outputs are specified, automatically creates a single output variable named `{step_id}.prompt` of type `text`.
- **Single Output Requirement**: Must have exactly one output variable - validation error occurs if multiple outputs are defined.
- **Input Flexibility**: Can accept any number of input variables that correspond to template placeholders.

--8<-- "components/PromptTemplate.md"

## Related Concepts

PromptTemplate steps are often used before [LLMInference](llm-inference.md) or [Agent](agent.md) steps to prepare prompts, and they consume [Variables](../Concepts/variable.md) for dynamic content generation.

## Example Usage

### Basic Prompt Template

```yaml
id: simple_prompt_app

flows:
  - id: basic_prompt_flow
    steps:
      - id: create_prompt
        template: "Please analyze the following text: {content}"
        inputs:
          - id: content
            type: text
        outputs:
          - id: analysis_prompt
            type: text
      
      - id: analyze_text
        model: gpt-4o
        inputs:
          - id: prompt
            type: text
        outputs:
          - id: analysis_result
            type: text
```

### Multi-Variable Template

```yaml
flows:
  - id: complex_prompt_flow
    steps:
      - id: build_context_prompt
        template: |
          You are a {role} expert with {experience} years of experience.
          
          Context: {context}
          
          Task: {task}
          
          Please provide your analysis focusing on {focus_areas}.
        inputs:
          - id: role
            type: text
          - id: experience
            type: text
          - id: context
            type: text
          - id: task
            type: text
          - id: focus_areas
            type: text
        outputs:
          - id: expert_prompt
            type: text
```

### Template for Data Processing

```yaml
flows:
  - id: data_analysis_flow
    steps:
      - id: format_data_prompt
        template: |
          Analyze the following dataset:
          
          Data Type: {data_type}
          Size: {data_size} records
          Columns: {column_names}
          
          Sample Data:
          {sample_data}
          
          Please provide:
          1. Data quality assessment
          2. Key insights
          3. Recommended next steps
        inputs:
          - id: data_type
            type: text
          - id: data_size
            type: text
          - id: column_names
            type: text
          - id: sample_data
            type: text
        outputs:
          - id: data_analysis_prompt
            type: text
      
      - id: analyze_dataset
        model: gpt-4o
        system_message: "You are a data analyst expert."
        inputs:
          - id: prompt
            type: text
        outputs:
          - id: data_insights
            type: text
```

### Conditional Prompt Building

```yaml
flows:
  - id: adaptive_prompt_flow
    steps:
      - id: basic_prompt
        template: "Summarize this text: {text}"
        inputs:
          - id: text
            type: text
        outputs:
          - id: basic_summary_prompt
            type: text
      
      - id: detailed_prompt
        template: |
          Provide a detailed analysis of the following text:
          
          Text: {text}
          
          Please include:
          - Main themes
          - Key arguments
          - Supporting evidence
          - Tone and style
          - Target audience
        inputs:
          - id: text
            type: text
        outputs:
          - id: detailed_analysis_prompt
            type: text
      
      - id: choose_prompt_type
        inputs:
          - id: analysis_type
            type: text
        equals:
          id: detailed_analysis
          type: text
        then: detailed_prompt
        else: basic_prompt
```

### Template Chaining

```yaml
flows:
  - id: prompt_pipeline
    steps:
      - id: context_template
        template: "Context: {background_info}"
        inputs:
          - id: background_info
            type: text
        outputs:
          - id: context_section
            type: text
      
      - id: question_template
        template: "Question: {user_question}"
        inputs:
          - id: user_question
            type: text
        outputs:
          - id: question_section
            type: text
      
      - id: final_prompt_template
        template: |
          {context}
          
          {question}
          
          Instructions: {instructions}
        inputs:
          - id: context
            type: text
          - id: question
            type: text
          - id: instructions
            type: text
        outputs:
          - id: complete_prompt
            type: text
      
      - id: process_request
        model: gpt-4o
        inputs:
          - id: prompt
            type: text
        outputs:
          - id: response
            type: text
```

### Template with Automatic Output

```yaml
flows:
  - id: auto_output_flow
    steps:
      - id: simple_template
        # No outputs defined - will automatically create "simple_template.prompt"
        template: "Translate '{text}' to {target_language}"
        inputs:
          - id: text
            type: text
          - id: target_language
            type: text
      
      - id: translate_text
        model: translation_model
        inputs:
          - id: prompt
            type: text
        outputs:
          - id: translation
            type: text
```
