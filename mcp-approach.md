# QType MCP – Goals, Design, and Model-Facing Context

## Overview

QType is a domain-specific language (DSL) for defining AI workflows as YAML.
It emphasizes explicit structure, strong validation, and deterministic execution
over ad-hoc prompting or opaque agent logic.

The **QType MCP server** exists to bridge general-purpose LLMs with the QType DSL
in a reliable, iterative, and machine-friendly way.

The MCP server is not a chatbot.
It is a **domain boundary** that exposes:
- authoritative validation
- structured examples and patterns
- discoverable constraints and rules

so that an LLM can *author, validate, and repair* QType YAML correctly.

---

## Primary Objective

Enable an LLM to reliably perform the loop:

> idea → YAML → validate → fix → revalidate → run

without relying on:
- large prompt injections
- human-curated context
- undocumented assumptions

Validation is the final arbiter of correctness.

---

## Core Design Principles

### 1. Validation Is the Source of Truth

- The validator defines correctness, not documentation or examples.
- All YAML must pass validation before it is considered usable.
- Validation errors must be:
  - stable
  - structured
  - explainable
  - referenceable by ID

The MCP server must surface validation output directly and faithfully.

---

### 2. Knowledge Must Be Discoverable by the Model

Critical domain knowledge must be exposed via **tools**, not static prose.

If the model might need information more than once, it must be retrievable
programmatically.

This includes:
- examples
- patterns
- schema summaries
- constraints
- error explanations

---

### 3. Tools Over Prompts

- Tools are callable by the model and support agentic workflows.
- Prompts are *entry points*, not knowledge stores.
- Prompts should initialize behavior, not encode rules.

The model should be instructed to use tools to learn the DSL.

---

### 4. Structured Data Over Prose

- Prefer JSON / YAML / typed objects over free text.
- Tool responses should be:
  - minimal
  - targeted
  - composable

Large README-style text blobs should be avoided in MCP responses.

---

## MCP Server Responsibilities

The QType MCP server runs locally on the user’s machine and typically:

- Wraps QType CLI commands
- Exposes structured documentation and examples
- Executes validation
- Enables iterative repair loops

### The MCP Server SHOULD:

- Provide self-discoverable tools for examples, schema, and rules
- Return machine-readable diagnostics
- Support repeated querying during a single interaction
- Stay tightly aligned with the validator implementation

### The MCP Server SHOULD NOT:

- Duplicate business logic from the validator
- Require manual context attachment by users
- Depend on editor- or vendor-specific features

---

## Canonical Tool Surfaces

### Project Identity and Mental Model

```text
qtype.about() -> {
  name
  purpose
  mental_model
  constraints
  non_goals
  version
}
```

This establishes:
- what QType is
- what it is not
- what assumptions are safe
- how the DSL should be approached

The model is expected to call this early in any workflow.

---

### Examples and Patterns

Backed by the repository’s `examples/` directory.

```text
qtype.list_examples() -> [
  { id, description }
]

qtype.get_example(id) -> yaml
```

Examples should be:
- minimal
- valid
- idiomatic

The model is expected to adapt examples rather than invent structure.

---

### Schema and Constraints (Summary)

```text
qtype.get_schema_summary() -> {
  required_fields
  step_structure
  typing_rules
  common_pitfalls
}
```

This is a **summary**, not a replacement for validation.
It provides orientation, not enforcement.

---

### Validation (Authoritative)

```text
qtype.validate(yaml_text | file_path) -> {
  valid: boolean
  diagnostics: [
    {
      id
      message
      location
      severity
      fix_hint
    }
  ]
}
```

Diagnostics should:
- reference stable rule IDs
- point to exact locations when possible
- include actionable fix hints

Optional extension:

```text
qtype.explain_error(id) -> detailed guidance
```

---

### Patch-Based Repair (Optional but Preferred)

```text
qtype.apply_patch(file_path, patch) -> ok
```

This encourages:
- minimal diffs
- deterministic edits
- fast convergence

---

## Prompts: Entry Points Only

Prompts are **manually selected** by the user or client UI.

They are used to:
- initialize a workflow
- establish expectations
- instruct the model to rely on tools and validation

Prompts must NOT contain:
- schema definitions
- DSL rules
- large examples

Example prompt intent:
> “Create a QType flow from an idea. Use QType tools to explore examples and constraints. Always validate before returning YAML.”

---

## Expected Model Behavior

A compliant LLM interacting with QType MCP should:

1. Call `qtype.about`
2. Explore examples or schema summaries if needed
3. Generate YAML
4. Validate YAML
5. Repair issues based on diagnostics
6. Revalidate until clean

Correctness is defined by validation, not confidence.

---

## Design Intent

The QType MCP is designed so that:

- Improving documentation improves agent performance
- Validation errors become the living specification
- Humans and models share the same sources of truth

The MCP server is not an assistant.
It is a **typed interface between a general-purpose LLM and a strongly-constrained DSL**.