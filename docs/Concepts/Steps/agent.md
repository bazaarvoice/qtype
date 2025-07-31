# Agent

Agent is a specialized LLMInference step that combines language model capabilities with tool access, enabling AI assistants that can perform actions, make API calls, execute functions, and interact with external systems. Agents represent autonomous AI entities that can reason about tasks and use available tools to accomplish objectives.

Agents extend the basic LLMInference functionality by providing access to a curated set of tools, allowing the AI to move beyond text generation to actual task execution and problem-solving in dynamic environments.

## Rules and Behaviors

- **Inherits LLMInference**: All LLMInference rules and behaviors apply (required model, automatic output, memory integration, etc.).
- **Required Tools**: The `tools` field is mandatory and specifies the list of tools available to the agent.
- **Tool Integration**: Can reference tools by ID string or embed tool configurations inline.
- **Decision Making**: The agent autonomously decides which tools to use based on the input and conversation context.
- **Multi-Step Execution**: Can perform multiple tool calls and reasoning steps within a single agent invocation.
- **Memory Awareness**: Leverages memory to maintain context across tool usage and conversations.

--8<-- "components/Agent.md"

## Related Concepts

Agent steps extend [LLMInference](llm-inference.md) and require [Model](../Concepts/model.md) configurations and [Tool](../Concepts/tool.md) access. They may use [Memory](../Concepts/memory.md) for persistent context and can be orchestrated within [Flows](../Concepts/flow.md).

## Example Usage

### Research Assistant Agent

```yaml
id: research_assistant_app

models:
  - id: agent_model
    provider: openai
    model_id: gpt-4o
    auth: openai_auth

tools:
  - id: web_search
    name: search_web
    description: "Search the web for current information"
    endpoint: "https://api.search.com/search"
    method: GET
    auth: search_auth
  
  - id: calculator
    name: calculate
    description: "Perform mathematical calculations"
    module_path: "math_tools"
    function_name: "calculate"

memories:
  - id: research_memory
    token_limit: 75000

flows:
  - id: research_workflow
    steps:
      - id: research_agent
        model: agent_model
        memory: research_memory
        tools: [web_search, calculator]
        system_message: |
          You are a research assistant that can search the web and perform 
          calculations. Use your tools to gather information and provide 
          accurate, well-researched answers.
        inputs:
          - id: research_question
            type: text
        outputs:
          - id: research_answer
            type: text
```

### Customer Support Agent

```yaml
tools:
  - id: ticket_lookup
    name: lookup_ticket
    description: "Look up customer support ticket details"
    endpoint: "https://api.helpdesk.com/tickets/{ticket_id}"
    method: GET
    auth: helpdesk_auth
  
  - id: update_ticket
    name: update_ticket_status
    description: "Update the status of a support ticket"
    endpoint: "https://api.helpdesk.com/tickets/{ticket_id}/status"
    method: PUT
    auth: helpdesk_auth
  
  - id: knowledge_search
    name: search_knowledge_base
    description: "Search the company knowledge base for solutions"
    index: support_knowledge_base

flows:
  - id: support_agent_flow
    steps:
      - id: support_agent
        model: support_model
        memory: support_memory
        tools: [ticket_lookup, update_ticket, knowledge_search]
        system_message: |
          You are a helpful customer support agent. Use your tools to:
          1. Look up ticket information
          2. Search for solutions in the knowledge base
          3. Update ticket status when appropriate
          
          Always be helpful, professional, and thorough.
        inputs:
          - id: customer_inquiry
            type: text
          - id: ticket_id
            type: text
        outputs:
          - id: support_response
            type: text
```

### Data Analysis Agent

```yaml
tools:
  - id: data_query
    name: query_database
    description: "Execute SQL queries against the data warehouse"
    module_path: "data_tools"
    function_name: "execute_query"
  
  - id: chart_generator
    name: create_chart
    description: "Generate charts and visualizations from data"
    module_path: "visualization_tools"
    function_name: "create_chart"
  
  - id: statistical_analysis
    name: analyze_statistics
    description: "Perform statistical analysis on datasets"
    module_path: "stats_tools"
    function_name: "statistical_summary"

flows:
  - id: data_analysis_flow
    steps:
      - id: data_analyst_agent
        model: analysis_model
        tools: [data_query, chart_generator, statistical_analysis]
        system_message: |
          You are a data analyst expert. Use your tools to:
          1. Query databases for relevant data
          2. Perform statistical analysis
          3. Create visualizations
          4. Provide insights and recommendations
        inputs:
          - id: analysis_request
            type: text
        outputs:
          - id: analysis_report
            type: text
```

### Multi-Tool Workflow Agent

```yaml
tools:
  - id: file_reader
    name: read_file
    description: "Read contents of files"
    module_path: "file_tools"
    function_name: "read_file"
  
  - id: email_sender
    name: send_email
    description: "Send emails to specified recipients"
    endpoint: "https://api.email.com/send"
    method: POST
    auth: email_auth
  
  - id: calendar_check
    name: check_calendar
    description: "Check calendar availability"
    endpoint: "https://api.calendar.com/events"
    method: GET
    auth: calendar_auth

flows:
  - id: workflow_automation
    steps:
      - id: automation_agent
        model: automation_model
        memory: workflow_memory
        tools: [file_reader, email_sender, calendar_check]
        system_message: |
          You are a workflow automation assistant. You can:
          1. Read and analyze files
          2. Send emails
          3. Check calendar availability
          
          Use these tools to help automate business processes.
        inputs:
          - id: automation_task
            type: text
        outputs:
          - id: automation_result
            type: text
```

### Embedded Tools Configuration

```yaml
flows:
  - id: embedded_tools_flow
    steps:
      - id: specialized_agent
        model: specialized_model
        tools:
          - id: custom_api_tool
            name: custom_api_call
            description: "Call a specialized API endpoint"
            endpoint: "https://api.specialized.com/process"
            method: POST
            auth:
              id: custom_auth
              type: api_key
              api_key: ${CUSTOM_API_KEY}
          
          - id: custom_function_tool
            name: process_data
            description: "Process data using custom algorithm"
            module_path: "custom_processing"
            function_name: "advanced_process"
        system_message: |
          You are a specialized agent with access to custom tools for 
          advanced data processing and API integration.
        inputs:
          - id: specialized_request
            type: text
        outputs:
          - id: specialized_result
            type: text
```

### Multi-Agent Collaboration

```yaml
flows:
  - id: multi_agent_workflow
    steps:
      - id: planning_agent
        model: planner_model
        tools: [calendar_check, task_analyzer]
        system_message: "You are a planning agent that breaks down complex tasks."
        inputs:
          - id: complex_task
            type: text
        outputs:
          - id: task_plan
            type: text
      
      - id: execution_agent
        model: executor_model
        tools: [file_reader, data_processor, email_sender]
        system_message: |
          You are an execution agent that carries out planned tasks. 
          Follow the provided plan and use your tools to complete each step.
        inputs:
          - id: execution_plan
            type: text
        outputs:
          - id: execution_results
            type: text
      
      - id: review_agent
        model: reviewer_model
        tools: [quality_checker, report_generator]
        system_message: |
          You are a review agent that validates completed work and 
          generates final reports.
        inputs:
          - id: work_results
            type: text
        outputs:
          - id: final_report
            type: text
```
