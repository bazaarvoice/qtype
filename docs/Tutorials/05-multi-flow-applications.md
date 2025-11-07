# Multi-Flow Applications

**Time:** 20 minutes  
**Prerequisites:** Tutorials 1-4  
**Example:** [`multi_flow_example.qtype.yaml`](https://github.com/bazaarvoice/qtype/blob/main/examples/multi_flow_example.qtype.yaml)

## What You'll Learn

In this tutorial, you'll learn how to:

- Create applications with multiple independent flows
- Understand variable scoping within flows
- Choose which flow to execute at runtime
- Design modular, reusable flows

## Why Multiple Flows?

So far, we've built applications with a single flow. But real-world applications often need multiple distinct workflows:

- Different use cases (e.g., "create customer" vs "update customer")
- Different entry points for different user roles
- Reusable sub-workflows for common operations
- A/B testing different approaches

**Key concept:** Each flow is independent with its own variables, inputs, and outputs. Variables in one flow cannot access variables in another flow - this isolation prevents naming conflicts and makes flows easier to reason about.

## The Multi-Flow Example

Our example application has three independent flows for customer data processing:

1. **`clean_names`** - Cleans and standardizes customer names
2. **`validate_names`** - Validates that names are legitimate person names
3. **`generate_profile`** - Generates complete customer profiles

Let's examine the structure:

```yaml
id: multi_flow_example
description: Multi-flow application demonstrating multiple independent flows

models:

- type: Model
    id: gpt4o-mini
    provider: openai
    model_id: gpt-4o-mini

flows:

- type: Flow
    id: clean_names
    # ... flow definition ...
  
  - type: Flow
    id: validate_names
    # ... flow definition ...
  
  - type: Flow
    id: generate_profile
    # ... flow definition ...
```

## Variable Scoping

Each flow defines its own variables that are completely isolated from other flows:

```yaml
flows:

- type: Flow
    id: clean_names
    variables:

- id: raw_name        # Only exists in clean_names flow
        type: text
      - id: clean_name      # Only exists in clean_names flow
        type: text
    
  - type: Flow
    id: validate_names
    variables:

- id: name_to_validate  # Only exists in validate_names flow
        type: text
      - id: validation_result # Only exists in validate_names flow
        type: text
```

**Important:** Even though both flows work with names, they use different variable names. The `clean_name` variable in `clean_names` is completely separate from `name_to_validate` in `validate_names`. This prevents accidental data leakage and makes each flow self-contained.

## Flow Inputs and Outputs

Each flow declares what inputs it requires and what outputs it produces:

```yaml
- type: Flow
  id: clean_names
  
  inputs:

- raw_name      # Required input - must be provided when running this flow
  
  outputs:

- clean_name    # Output - available in results after flow completes
```

This contract makes flows easy to understand and test in isolation.

## The Clean Names Flow

Let's examine the `clean_names` flow in detail:

```yaml
- type: Flow
  id: clean_names
  description: Clean and standardize customer names
  
  variables:

- id: raw_name
      type: text
    - id: clean_prompt
      type: text
    - id: clean_name
      type: text
  
  inputs:

- raw_name
  
  outputs:

- clean_name
  
  steps:
    # Step 1: Create prompt to clean the name
    - id: create_clean_prompt
      type: PromptTemplate
      template: "Clean this name by trimming whitespace and converting to title case: {{raw_name}}. Return ONLY the cleaned name, nothing else."
      inputs:

- raw_name
      outputs:

- clean_prompt
    
    # Step 2: Call LLM to clean the name
    - id: clean_step
      type: LLMInference
      model: gpt4o-mini
      inputs:

- clean_prompt
      outputs:

- clean_name
```

**Pattern:** Notice the `PromptTemplate` → `LLMInference` pattern. This is the standard way to work with LLMs in QType:

1. Use `PromptTemplate` to construct the prompt from variables
2. Pass the prompt to `LLMInference` to get the result

## Running Specific Flows

When you have multiple flows, you specify which one to run with the `-f` flag:

```bash
# Run the clean_names flow
uv run qtype run -f clean_names \
  -i '{"raw_name":"  john doe  "}' \
  examples/multi_flow_example.qtype.yaml
```

Output:
```
clean_name: John Doe
```

```bash
# Run the validate_names flow
uv run qtype run -f validate_names \
  -i '{"name_to_validate":"John Doe"}' \
  examples/multi_flow_example.qtype.yaml
```

Output:
```
validation_result: Valid
```

```bash
# Run the generate_profile flow
uv run qtype run -f generate_profile \
  -i '{"customer_name":"John Doe"}' \
  examples/multi_flow_example.qtype.yaml
```

Output:
```
customer_profile: Customer Profile for John Doe
Account Number: 12345678
Member Since: January 2020
Status: Gold
...
```

## Design Principles

When designing multi-flow applications:

**1. Keep flows focused:** Each flow should do one thing well. Our example has separate flows for cleaning, validation, and profile generation rather than one monolithic flow.

**2. Make flows reusable:** Design flows that can be used in multiple contexts. The `clean_names` flow could be used anywhere you need name standardization.

**3. Use clear variable names:** Since variables are scoped to their flow, use descriptive names that make sense within that flow's context.

**4. Define explicit contracts:** Always specify inputs and outputs clearly so flows can be understood and tested independently.

**5. Consider composition:** While this example shows independent flows, real applications might combine flows (using `InvokeFlow` step) to build complex workflows from simple building blocks.

## Testing Flows Independently

One major benefit of multi-flow applications is testability. You can validate and test each flow in isolation:

```bash
# Validate the entire application
uv run qtype validate examples/multi_flow_example.qtype.yaml

# Test just the clean_names flow
uv run qtype run -f clean_names -i '{"raw_name":"  JANE DOE  "}' examples/multi_flow_example.qtype.yaml

# Test just the validate_names flow
uv run qtype run -f validate_names -i '{"name_to_validate":"X Æ A-12"}' examples/multi_flow_example.qtype.yaml
```

This makes debugging easier - if something goes wrong, you can quickly isolate which flow is causing the issue.

## Visualizing Multi-Flow Applications

You can generate a mermaid diagram showing all flows:

```bash
uv run qtype visualize examples/multi_flow_example.qtype.yaml -o multi_flow.mmd
```

This creates a visual representation of your application's structure, showing all flows and their steps:

```mermaid
--8<-- "Tutorials/multi_flow.mmd"
```

The diagram shows:

- Three independent flows, each with its own variables and steps
- The `PromptTemplate` → `LLMInference` pattern in each flow
- A shared model resource (`gpt4o-mini`) used by all flows

## Next Steps

You now understand how to:

- ✅ Structure applications with multiple flows
- ✅ Scope variables within flows
- ✅ Run specific flows with the `-f` flag
- ✅ Design modular, testable workflows

**Challenge:** Extend the example to add a fourth flow called `format_report` that takes a `customer_name`, `validation_result`, and `customer_profile` as inputs and formats them into a professional customer service report.

## Reference

- [Flow Reference](../components/Flow.md)
- [PromptTemplate Reference](../components/PromptTemplate.md)
- [LLMInference Reference](../components/LLMInference.md)
