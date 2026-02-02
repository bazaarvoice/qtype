# Cheatsheet

## Abbreviated Shape Reference

### Application (Root Object)
```yaml
id: <string>                    # REQUIRED
flows: [<Flow>]                 # REQUIRED (at least one)
models: [<Model>]               # OPTIONAL
tools: [<Tool>]                 # OPTIONAL
types: [<CustomType>]           # OPTIONAL
```

### Flow
```yaml
type: Flow
id: <string>                    # REQUIRED
steps: [<Step>]                 # REQUIRED (at least one)
variables: [<Variable>]         # OPTIONAL
inputs: [<string>]              # OPTIONAL (Variable IDs)
outputs: [<string>]             # OPTIONAL (Variable IDs)
interface:                      # OPTIONAL
  type: <chat|form|agent>
```

### Variable
```yaml
type: Variable
id: <string>                    # REQUIRED
value_type: <type>              # REQUIRED (see Type Reference)
ui:                             # OPTIONAL
  type: <text-input|text-area|...>
  label: <string>
```

**Type Reference:**
- Primitives: `string`, `int`, `float`, `bool`
- Collections: `list`, `dict`
- Built-ins: `ChatMessage`, `Document`, `Embedding`
- Custom: Any CustomType `id`
- List syntax: `value_type: list` + `item_type: <type>`

### Model
```yaml
type: Model
id: <string>                    # REQUIRED
provider: <bedrock|openai|anthropic>  # REQUIRED
model_id: <string>              # REQUIRED
auth: <string>                  # OPTIONAL (AuthProvider ID)
```

### CustomType
```yaml
id: <string>                    # REQUIRED
fields:                         # REQUIRED (at least one)
  - name: <string>              # REQUIRED
    field_type: <type>          # REQUIRED
  - name: <string>
    field_type: list[<type>]
```

---

## Abbreviated Step Reference

### LLMInference
```yaml
type: LLMInference
id: <string>                    # REQUIRED
model: <string>                 # REQUIRED (Model ID)
inputs: [<string>]              # OPTIONAL (Variable IDs)
outputs: [<string>]             # OPTIONAL (Variable IDs)
system_message: <string>        # OPTIONAL
memory: <string>                # OPTIONAL (Variable ID for chat history)
```

### Agent
```yaml
type: Agent
id: <string>                    # REQUIRED
model: <string>                 # REQUIRED (Model ID)
tools: [<string>]               # REQUIRED (Tool IDs)
inputs: [<string>]              # OPTIONAL
outputs: [<string>]             # OPTIONAL
system_message: <string>        # OPTIONAL
```

### PromptTemplate
```yaml
type: PromptTemplate
id: <string>                    # REQUIRED
template: <string>              # REQUIRED (use {{var_id}} syntax)
inputs: [<string>]              # REQUIRED (Variable IDs to interpolate)
outputs: [<string>]             # REQUIRED (single Variable ID)
```

### InvokeFlow
```yaml
type: InvokeFlow
id: <string>                    # REQUIRED
flow: <string>                  # REQUIRED (Flow ID)
input_bindings:                 # REQUIRED (even if empty: {})
  <flow_input_id>: <local_var_id>
output_bindings:                # REQUIRED (even if empty: {})
  <local_var_id>: <flow_output_id>
```

### InvokeTool
```yaml
type: InvokeTool
id: <string>                    # REQUIRED
tool: <string>                  # REQUIRED (Tool ID)
input_bindings:                 # REQUIRED
  <tool_param>: <local_var_id>
output_bindings:                # REQUIRED
  <tool_output>: <local_var_id>
```

### Decoder
```yaml
type: Decoder
id: <string>                    # REQUIRED
format: <json|xml>              # REQUIRED
inputs: [<string>]              # REQUIRED (single Variable ID with text)
outputs: [<string>]             # REQUIRED (single Variable ID)
```

### Construct
```yaml
type: Construct
id: <string>                    # REQUIRED
output_type: <string>           # REQUIRED (CustomType ID)
field_bindings:                 # REQUIRED
  <field_name>: <var_id>
outputs: [<string>]             # REQUIRED (single Variable ID)
```

### VectorSearch
```yaml
type: VectorSearch
id: <string>                    # REQUIRED
index: <string>                 # REQUIRED (DocumentIndex ID)
inputs: [<string>]              # REQUIRED (query Variable ID)
outputs: [<string>]             # REQUIRED (results Variable ID)
top_k: <int>                    # OPTIONAL (default: 5)
```

### Explode
```yaml
type: Explode
id: <string>                    # REQUIRED
inputs: [<string>]              # REQUIRED (list Variable ID)
outputs: [<string>]             # REQUIRED (single item Variable ID)
```

### FileSource
```yaml
type: FileSource
id: <string>                    # REQUIRED
path: <string>                  # REQUIRED
outputs: [<string>]             # REQUIRED (Variable ID)
```

## Critical Rules

### ID Rules
- All `id` fields must be unique within their scope
- IDs must be valid identifiers (alphanumeric + underscore/hyphen)
- Reference other objects by their exact `id` string

### Variable Rules
- Variables in `inputs`/`outputs` must be defined in `variables` list
- Variables must have `value_type` specified
- List variables REQUIRE `item_type` field
- Variable types must match their usage in steps

### Step Rules
- Steps execute in order within `steps` array
- Step `inputs` must reference existing variables (from previous steps or flow inputs)
- Step `outputs` create or update variables for subsequent steps
- All referenced Model/Tool/Flow/CustomType IDs must exist

### Binding Rules
- `input_bindings`: Map local variables TO external inputs
  - Format: `{external_input_name: local_variable_id}`
- `output_bindings`: Map external outputs TO local variables
  - Format: `{local_variable_id: external_output_name}`
- Both must be present even if empty: `{}`

### Template Rules
- Use `{{variable_id}}` syntax only
- All variables in template must be in `inputs` list
- Template must be a single string (use `\n` for newlines)

### Type Rules
- Decoder outputs must match expected structure
- Construct `field_bindings` must map to all required CustomType fields
- List operations (Explode/Collect) require matching list types
