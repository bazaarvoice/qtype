# Referencing Entities by ID

One of QType's features is the ability to define reusable components once and reference them by their unique ID throughout your application. This promotes modularity, reduces duplication, and makes your specifications easier to maintain.

## How It Works

QType supports two ways to specify most components:

1. **Inline Definition**: Define the component directly where you use it
2. **Reference by ID**: Define the component elsewhere and reference it by its unique ID

The QType validation and resolution system automatically resolves ID references to their actual object definitions, ensuring all components are properly connected.

## Basic Reference Pattern

### Models

Instead of repeating model configurations:

```yaml
# ❌ Repetitive inline definitions
id: my_app
flows:
  - id: flow1
    steps:
      - id: step1
        model:
          id: gpt-4
          provider: openai
          auth:
            id: openai_auth
            type: api_key
            api_key: ${OPENAI_KEY}
      - id: step2  
        model:
          id: gpt-4
          provider: openai
          auth:
            id: openai_auth
            type: api_key
            api_key: ${OPENAI_KEY}
```

Define once and reference by ID:

```yaml
# ✅ Clean reference-based approach
id: my_app

# Define reusable components at the application level
auths:
  - id: openai_auth
    type: api_key
    api_key: ${OPENAI_KEY}

models:
  - id: gpt-4
    provider: openai
    auth: openai_auth  # Reference auth by ID

flows:
  - id: flow1
    steps:
      - id: step1
        model: gpt-4  # Reference model by ID
      - id: step2
        model: gpt-4  # Reuse the same model
```

### Variables

Variables can be defined once and referenced across multiple steps:

```yaml
id: variable_reuse_example

# Define shared variables
variables:
  - id: user_question
    type: text
  - id: llm_response
    type: text
  - id: formatted_output
    type: text

flows:
  - id: process_question
    steps:
      - id: llm_step
        model:
          id: gpt-4
          provider: openai
        inputs:
          - user_question  # Reference by ID
        outputs:
          - llm_response   # Reference by ID

      - id: format_step
        template: "Response: {llm_response}"
        inputs:
          - llm_response   # Reuse the same variable
        outputs:
          - formatted_output
```

## Advanced Reference Patterns

### Custom Types and Complex Data Structures

```yaml
id: type_reference_example

# Define reusable custom types
types:
  - id: Person
    properties:
      name: text
      age: int
      email: text
  - id: PersonList
    properties:
      items: list[Person]

# Define variables using custom types
variables:
  - id: current_user
    type: Person  # Reference custom type by ID
  - id: all_users
    type: PersonList  # Reference array type by ID

flows:
  - id: user_management
    steps:
      - id: get_user
        inputs:
          - id: user_id
            type: text
        outputs:
          - current_user  # Uses Person type

      - id: list_users
        outputs:
          - all_users  # Uses PersonList type
```

## Best Practices

### 1. Define Components at the Appropriate Level
- **Application-level**: Components used across multiple flows
- **Flow-level**: Components specific to one flow
- **Step-level**: Simple, one-off configurations

### 2. Use Descriptive IDs
```yaml
# ✅ Clear and descriptive
models:
  - id: openai_gpt4_chat
  - id: anthropic_claude_reasoning

# ❌ Unclear
models:
  - id: model1
  - id: m2
```

### 3. Group Related Components
```yaml
# ✅ Well-organized
auths:
  - id: openai_auth
  - id: anthropic_auth

models:
  - id: gpt4_model
    auth: openai_auth
  - id: claude_model  
    auth: anthropic_auth
```

### 4. Leverage References for Configuration Management
```yaml
# Different environments can reference different components
# development.qtype.yaml
models:
  - id: main_model
    provider: openai
    model_id: gpt-3.5-turbo  # Cheaper for dev

# production.qtype.yaml  
models:
  - id: main_model
    provider: openai
    model_id: gpt-4o         # Better for prod
```

## Validation and Error Handling

QType's validation system ensures:

1. **Unique IDs**: No duplicate component IDs within the same scope
2. **Valid References**: All ID references resolve to actual components
3. **Type Safety**: Referenced components match expected types

Common validation errors:

```yaml
# ❌ This will fail - duplicate ID
models:
  - id: gpt-4
    provider: openai
  - id: gpt-4  # Error: Duplicate ID
    provider: anthropic

# ❌ This will fail - missing reference  
flows:
  - id: my_flow
    steps:
      - model: nonexistent_model  # Error: Reference not found
```

The reference-by-ID system makes QType specifications more maintainable, reusable, and easier to understand by eliminating duplication and creating clear component relationships.

