# APITool

An APITool step enables HTTP API endpoint invocation within QType applications. It provides a standardized way to integrate external services, REST APIs, and web services into your workflows. APITool handles HTTP methods, authentication, headers, and request/response processing automatically.

This step type is essential for building applications that need to interact with external data sources, microservices, or third-party APIs while maintaining consistent error handling and data flow within the QType ecosystem.

## Rules and Behaviors

- **HTTP Method Support**: Supports all standard HTTP methods (GET, POST, PUT, DELETE, PATCH, etc.) for comprehensive API integration.
- **Authentication Integration**: Can use [AuthorizationProvider](../Concepts/authorization-provider.md) objects for secure API access with various auth methods.
- **Header Management**: Supports custom HTTP headers for API requirements like content types, API keys, or custom headers.
- **Response Processing**: Automatically processes API responses and makes them available to subsequent steps in the workflow.
- **Error Handling**: Provides structured error handling for HTTP status codes, network issues, and malformed responses.
- **Variable Integration**: Input and output variables enable dynamic endpoint construction and response data extraction.
- **URL Construction**: Endpoint URLs can be dynamic and constructed from input variables at runtime.

## Core Component

--8<-- "components/APITool.md"

## Related Concepts

APITool steps often work with [AuthorizationProvider](../Concepts/authorization-provider.md) for authentication, can be orchestrated in [Flows](../Concepts/flow.md), and may feed data to [Models](../Concepts/model.md) for AI processing. They're commonly used alongside [PythonFunctionTool](python-function-tool.md) and [Condition](condition.md) steps for complete integration workflows.

## Example Usage

### Basic API Call

```yaml
flows:
  - id: weather_api_flow
    steps:
      - id: get_weather
        endpoint: "https://api.weather.com/v1/current"
        method: GET
        headers:
          Accept: "application/json"
        inputs:
          - id: city
            type: text
        outputs:
          - id: weather_data
            type: text
```

### Authenticated API Integration

```yaml
authorization_providers:
  - id: api_auth
    type: bearer_token
    token: "${API_TOKEN}"

flows:
  - id: secure_api_flow
    steps:
      - id: fetch_user_data
        endpoint: "https://api.service.com/users/{user_id}"
        method: GET
        auth: api_auth
        headers:
          Content-Type: "application/json"
          X-Client-Version: "1.0"
        inputs:
          - id: user_id
            type: text
        outputs:
          - id: user_profile
            type: text
      
      - id: process_user_data
        model: gpt-4o
        system_message: "Analyze the user profile data and extract key insights."
        inputs:
          - id: profile_data
            type: text
        outputs:
          - id: user_insights
            type: text
```

### POST Request with Dynamic Data

```yaml
flows:
  - id: data_submission_flow
    steps:
      - id: prepare_payload
        module_path: "data_utils"
        function_name: "format_submission"
        inputs:
          - id: raw_data
            type: text
        outputs:
          - id: formatted_payload
            type: text
      
      - id: submit_data
        endpoint: "https://api.service.com/submissions"
        method: POST
        headers:
          Content-Type: "application/json"
        inputs:
          - id: submission_data
            type: text
        outputs:
          - id: submission_response
            type: text
      
      - id: handle_response
        inputs:
          - id: response_data
            type: text
        equals:
          id: success_status
          type: text
        then:
          id: success_handler
          template: "Submission successful: {response}"
        else:
          id: error_handler
          template: "Submission failed: {error}"
```

### Multi-API Workflow

```yaml
authorization_providers:
  - id: service_a_auth
    type: api_key
    key: "${SERVICE_A_KEY}"
  
  - id: service_b_auth
    type: bearer_token
    token: "${SERVICE_B_TOKEN}"

flows:
  - id: multi_service_integration
    steps:
      - id: fetch_from_service_a
        endpoint: "https://service-a.com/api/data"
        method: GET
        auth: service_a_auth
        inputs:
          - id: query_param
            type: text
        outputs:
          - id: service_a_data
            type: text
      
      - id: enrich_with_service_b
        endpoint: "https://service-b.com/api/enrich"
        method: POST
        auth: service_b_auth
        headers:
          Content-Type: "application/json"
        inputs:
          - id: data_to_enrich
            type: text
        outputs:
          - id: enriched_data
            type: text
      
      - id: synthesize_results
        model: gpt-4o
        system_message: "Combine and analyze data from multiple sources."
        inputs:
          - id: source_a_data
            type: text
          - id: source_b_data
            type: text
        outputs:
          - id: final_analysis
            type: text
```
