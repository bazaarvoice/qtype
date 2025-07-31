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

## Example Usage

### Tools as Direct Steps

```yaml
id: tool_workflow_app

auths:
  - id: api_auth
    type: api_key
    api_key: "${API_KEY}"

tools:
  - id: fetch_data_tool
    name: fetch_external_data
    description: "Retrieve data from external API"
    endpoint: "https://api.service.com/data"
    method: GET
    auth: api_auth
  
  - id: process_tool
    name: process_data
    description: "Process and validate data"
    module_path: "processing"
    function_name: "validate_and_process"

flows:
  - id: data_pipeline
    steps:
      # Using API tool as a step
      - id: fetch_data_tool
        inputs:
          - id: query_param
            type: text
        outputs:
          - id: raw_data
            type: text
      
      # Using Python function tool as a step
      - id: process_tool
        inputs:
          - id: data_to_process
            type: text
        outputs:
          - id: processed_data
            type: text
```

### Tools for Agent Use

```yaml
id: agent_tools_app

models:
  - id: agent_model
    provider: openai
    model_id: gpt-4o
    auth: openai_auth

tools:
  - id: calculator_tool
    name: calculate
    description: "Perform mathematical calculations"
    module_path: "math_utils"
    function_name: "calculate"
  
  - id: web_search_tool
    name: search_web
    description: "Search the web for information"
    endpoint: "https://api.search.com/search"
    method: GET
    auth: search_auth
  
  - id: email_tool
    name: send_email
    description: "Send email notifications"
    endpoint: "https://api.email.com/send"
    method: POST
    auth: email_auth

flows:
  - id: intelligent_assistant
    steps:
      - id: assistant_agent
        model: agent_model
        tools: [calculator_tool, web_search_tool, email_tool]
        system_message: |
          You are an intelligent assistant with access to calculation, 
          web search, and email capabilities. Use these tools to help 
          users accomplish their tasks.
        inputs:
          - id: user_request
            type: text
        outputs:
          - id: assistant_response
            type: text
```