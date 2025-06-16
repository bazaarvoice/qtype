Here's a comprehensive list of **semantic validation rules** for the `QTypeSpec` schema. These rules go beyond structural validation and ensure internal consistency, correct references, and logical cohesion.

---

### 🔐 **1. Unique IDs**

Ensure that every ID in these collections is unique:

* `Model.id`
* `Input.id`
* `Prompt.id`
* `Output.id` (referenced in prompts or flows)
* `Memory.id`
* `Tool.id`
* `ToolProvider.id`
* `AuthorizationProvider.id`
* `Feedback.id`
* `Retriever.id`
* `Step.id`
* `Flow.id`

---

### 🔁 **2. Referential Integrity**

Any string that is a reference to another component **must exist**:

* `Prompt.input_vars[]` must refer to existing `Input.id`
* `Prompt.output_vars[]` must refer to existing `Output.id`
* `Step.component` must refer to an existing:

  * `Prompt.id` if `type = prompt`
  * `Tool.id` if `type = tool`
  * `Flow.id` if `type = flow`
  * `BaseRetriever.id` if `type = retriever`
* `Step.input_vars[]` and `Step.output_vars[]` must refer to:

  * Declared `Input.id` and/or `Output.id`
* `VectorDBRetriever.embedding_model` and `Memory.embedding_model` must refer to `EmbeddingModel.id`
* `ToolProvider.auth` must refer to `AuthorizationProvider.id`
* `ToolProvider.tools[].input_schema` and `output_schema` can be arbitrarily structured, but may benefit from future cross-validation
* `Flow.memory[]` must refer to `Memory.id`

---

### 🔄 **3. Flow Validation**

For each `Flow`:

* All `Step.id` values must be **unique within the flow**
* All `Flow.steps[]` entries must be:

  * A `Step` object with a valid `type` and `component`
  * OR a string referring to a valid `Flow.id`
* `Flow.inputs[]` and `outputs[]` must refer to valid `Input.id` and `Output.id`
* `Flow.conditions[].then[]` and `else_[]` must refer to valid `Step.id` or nested `Flow.id`
* If `Flow.mode == chat`:

  * `Flow.memory[]` must be set (optional but valid)
* If `Flow.mode != chat`:

  * `Flow.memory[]` must be `None` or omitted

---

### 🧠 **4. Memory vs Retriever**

* `Memory` is global/session state and should **not** be used as a `Step`
* `Retriever` is used **within a flow step**
* `Memory.embedding_model` and `Retriever.embedding_model` can share the same model but **serve different purposes**
* Enforce that `Memory.id` is only used in `Flow.memory[]`, not as a `Step.component`

---

### 🛠️ **5. Tooling Rules**

* `ToolProvider.tools[].id` must be unique **within that provider**
* A `Tool` must define both `input_schema` and `output_schema`
* If using `ToolProvider.openapi_spec`, `tools[]` may be empty — you will populate via parsing
* `Tool.name` should be unique across all tools in the same provider

---

### 🧾 **6. Model + Embedding Rules**

* `Model.provider` and `EmbeddingModel.provider` should be consistent naming (e.g., `openai`, `cohere`)
* Only `Model` supports `inference_params`
* `EmbeddingModel.model` must not be used in a `Model`

---

### 🧪 **7. Prompt Requirements**

* Must define either `template` or `path`, but not both
* All variables in `input_vars` and `output_vars` must resolve to declared `Input` and `Output`
* Template validation: (future) optionally confirm that template uses all listed `input_vars`

---

### 🗂️ **8. General Best Practices**

* No circular references in `Flow.steps[]`
* Avoid orphaned components (e.g., a `Prompt` defined but never used)
* Every referenced variable or ID must be **visible** in the context it's used

---

Would you like me to help scaffold this validator into your `ir/resolver.py`, or start with a function that implements these checks step-by-step?
