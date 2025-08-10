# File Inclusion and Modular YAML

QType supports including external files in your YAML specifications, allowing you to break large configurations into smaller, manageable modules and reuse common components across multiple applications.

## Include Directives

### `!include` - YAML File Inclusion

The `!include` directive loads and parses external YAML files, merging their content into your main specification:

```yaml
# main.qtype.yaml
id: main_app

# Include reusable components from other files
auths: !include common/auth.qtype.yaml
models: !include common/models.qtype.yaml
tools: !include common/tools.qtype.yaml
## Conditional References

References work seamlessly with conditional logic:

```yaml
id: conditional_example

tools:
  - id: email_tool
    name: send_email
    description: Send an email
    # ... tool definition
  
  - id: slack_tool
    name: send_slack
    description: Send Slack message
    # ... tool definition

flows:
  - id: notification_flow
    steps:
      - id: check_preference
        # ... step to get user preference
      
      - id: send_notification
        equals:
          id: notification_type
          type: text
        then:
          id: email_step
          tools:
            - email_tool  # Reference by ID
        else:
          id: slack_step
          tools:
            - slack_tool  # Reference by ID
```

flows:
  - id: main_flow
    steps:
      - id: llm_step
        model: shared_gpt4  # Defined in models.qtype.yaml
        system_message: !include_raw prompts/system_message.txt
```

```yaml
# common/models.qtype.yaml
- id: shared_gpt4
  provider: openai
  auth: shared_openai_auth
  model_id: gpt-4
  
- id: shared_claude
  provider: anthropic
  auth: shared_anthropic_auth
  model_id: claude-3-5-sonnet-20241022
```

```yaml
# common/auth.qtype.yaml
- id: shared_openai_auth
  type: api_key
  api_key: ${OPENAI_KEY}

- id: shared_anthropic_auth
  type: api_key
  api_key: ${ANTHROPIC_KEY}
```

### `!include_raw` - Raw Text Inclusion

The `!include_raw` directive loads external text files as raw strings, useful for prompts, templates, or documentation:

```yaml
# Application with external prompt files
id: prompt_app

flows:
  - id: chat_flow
    steps:
      - id: system_setup
        model: gpt-4
        system_message: !include_raw prompts/expert_assistant.txt
        
      - id: user_interaction
        model: gpt-4
        template: !include_raw templates/response_format.txt
```

```txt
# prompts/expert_assistant.txt
You are an expert AI assistant with deep knowledge across multiple domains.
Always provide accurate, helpful, and well-structured responses.

When answering questions:
1. Be concise but thorough
2. Provide examples when helpful
3. Cite sources when making factual claims
4. Ask for clarification if the question is ambiguous
```

```txt
# templates/response_format.txt
Based on the user's question: "{{user_question}}"

Please provide a response in the following format:
- **Summary**: Brief answer to the question
- **Details**: More comprehensive explanation
- **Examples**: Relevant examples if applicable
- **Next Steps**: Suggested follow-up actions
```

## File Path Resolution

QType supports multiple path types and protocols:

### Local File Paths

```yaml
# Relative paths (relative to the current YAML file)
models: !include ../shared/models.yaml
prompts: !include_raw ./prompts/system.txt

# Absolute paths
config: !include /etc/qtype/global-config.yaml
```

### Remote URLs

```yaml
# HTTP/HTTPS URLs
shared_config: !include https://config.example.com/qtype/base.yaml
prompt_library: !include_raw https://prompts.example.com/expert-system.txt

# GitHub URLs (via fsspec)
tools: !include github://company/qtype-configs/main/tools.yaml
```

### Cloud Storage

```yaml
# S3 URLs
production_config: !include s3://company-configs/qtype/prod.yaml
training_data: !include_raw s3://data-bucket/prompts/training.txt
```

## Environment-Specific Configurations

Use file inclusion to manage different environments:

```yaml
# base.qtype.yaml - Common configuration
id: my_app

# Include environment-specific overrides
models: !include environments/${ENV:-development}/models.yaml
auths: !include environments/${ENV:-development}/auth.yaml

flows:
  - id: main_flow
    steps:
      - id: llm_step
        model: primary_model
        system_message: !include_raw prompts/base_system.txt
```

```yaml
# environments/development/models.yaml
- id: primary_model
  provider: openai
  model_id: gpt-3.5-turbo  # Cheaper for development
  auth: dev_openai_auth

- id: secondary_model
  provider: anthropic
  model_id: claude-3-haiku-20240307  # Fast for testing
  auth: dev_anthropic_auth
```

```yaml
# environments/production/models.yaml
- id: primary_model
  provider: openai
  model_id: gpt-4o  # Best quality for production
  auth: prod_openai_auth
  inference_params:
    temperature: 0.1
    max_tokens: 4000

- id: secondary_model
  provider: anthropic
  model_id: claude-3-5-sonnet-20241022  # High quality fallback
  auth: prod_anthropic_auth
```

## Nested Inclusions

Files can include other files, creating a hierarchy of modular components:

```yaml
# main.qtype.yaml
id: complex_app
flows: !include flows/index.yaml
```

```yaml
# flows/index.yaml
- id: data_processing
  description: !include_raw descriptions/data_processing.md
  steps: !include flows/data_processing_steps.yaml

- id: user_interaction  
  description: !include_raw descriptions/user_interaction.md
  steps: !include flows/user_interaction_steps.yaml
```

```yaml
# flows/data_processing_steps.yaml
- id: extract_step
  tools: !include ../tools/extraction.yaml
  
- id: transform_step
  model: !include ../models/transformation_model.yaml
  template: !include_raw ../templates/transform_prompt.txt

- id: load_step
  tools: !include ../tools/database.yaml
```

## Component Libraries

Create reusable component libraries:

```yaml
# libraries/ai-models.yaml
- id: gpt4_creative
  provider: openai
  model_id: gpt-4
  auth: openai_auth
  inference_params:
    temperature: 0.8
    max_tokens: 2000

- id: gpt4_analytical  
  provider: openai
  model_id: gpt-4
  auth: openai_auth
  inference_params:
    temperature: 0.1
    max_tokens: 4000

- id: claude_creative
  provider: anthropic
  model_id: claude-3-5-sonnet-20241022
  auth: anthropic_auth
  inference_params:
    temperature: 0.7
    max_tokens: 8000
```

```yaml
# libraries/common-tools.yaml
- id: web_search
  name: search_web
  description: Search the web for current information
  endpoint: https://api.search.com/v1/search
  method: GET
  auth: search_api_auth
  
- id: email_sender
  name: send_email
  description: Send emails via SMTP
  function_name: send_email
  module_path: qtype.commons.email
```

```yaml
# applications/research-assistant.yaml
id: research_assistant

# Import component libraries
models: !include ../libraries/ai-models.yaml
tools: !include ../libraries/common-tools.yaml

flows:
  - id: research_flow
    steps:
      - id: search_step
        tools:
          - web_search  # From imported library
          
      - id: analysis_step
        model: gpt4_analytical  # From imported library
        system_message: !include_raw prompts/research_analysis.txt
```

## Best Practices

### 1. Organize by Logical Groupings

```
project/
├── qtype/
│   ├── main.qtype.yaml
│   ├── auth/
│   │   ├── development.yaml
│   │   └── production.yaml
│   ├── models/
│   │   ├── openai.yaml
│   │   └── anthropic.yaml
│   ├── tools/
│   │   ├── api-tools.yaml
│   │   └── python-tools.yaml
│   └── prompts/
│       ├── system-messages/
│       └── templates/
```

### 2. Use Consistent Naming Conventions

```yaml
# ✅ Clear, consistent naming
models: !include models/openai-models.yaml
tools: !include tools/api-tools.yaml
prompts: !include_raw prompts/system-messages/expert.txt

# ❌ Inconsistent naming  
models: !include models.yaml
tools: !include tool_definitions.yml
prompts: !include_raw prompt.txt
```

### 3. Document File Dependencies

```yaml
# main.qtype.yaml
# Dependencies:
# - auth/production.yaml (auth providers)
# - models/openai.yaml (LLM models)
# - tools/api-tools.yaml (external API tools)
# - prompts/system.txt (system message)

id: production_app
auths: !include auth/production.yaml
models: !include models/openai.yaml
tools: !include tools/api-tools.yaml

flows:
  - id: main_flow
    steps:
      - model: production_gpt4
        system_message: !include_raw prompts/system.txt
```

### 4. Use Environment Variables for Dynamic Paths

```yaml
# Load different configurations based on environment
models: !include models/${QTYPE_ENV:-development}.yaml
auths: !include auth/${QTYPE_ENV:-development}.yaml

# Load user-specific configurations
user_settings: !include users/${USER}/settings.yaml
```

## Error Handling

QType provides clear error messages for file inclusion issues:

```yaml
# File not found
models: !include missing-file.yaml
# Error: Failed to load included file 'missing-file.yaml': [Errno 2] No such file or directory

# Invalid YAML syntax in included file
tools: !include malformed-tools.yaml  
# Error: Failed to load included file 'malformed-tools.yaml': while parsing...

# Missing environment variable in included file
config: !include config-with-missing-vars.yaml
# Error: Environment variable 'REQUIRED_VAR' is required but not set
```

## Security Considerations

### 1. Path Traversal Protection
QType resolves paths relative to the including file, preventing unauthorized access:

```yaml
# Safe - resolves relative to current file
config: !include ../shared/config.yaml

# Potentially unsafe - absolute paths should be used carefully
config: !include /etc/passwd  # Will fail with appropriate error
```

### 2. Environment Variable Security
Use environment variables for sensitive data in included files:

```yaml
# auth.yaml - Don't commit secrets
- id: production_auth
  type: api_key
  api_key: ${PROD_API_KEY}  # Load from environment
```

### 3. URL Validation
Remote URLs are validated and must use secure protocols where appropriate:

```yaml
# ✅ Secure HTTPS
config: !include https://secure-config.example.com/config.yaml

# ⚠️ HTTP should be avoided for sensitive configs
config: !include http://config.example.com/config.yaml
```

File inclusion makes QType specifications more modular, maintainable, and suitable for complex, multi-environment deployments while keeping sensitive information secure and configurations organized.
