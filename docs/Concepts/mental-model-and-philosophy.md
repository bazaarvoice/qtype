# Mental Model & Philosophy

## What is QType?

**QType is a domain-specific language (DSL) for rapid prototyping of AI applications.**

Qtype is a declarative, text-based language that lets you specify *what* your AI application should do, not *how* to do it. You write YAML specifications that describe flows, steps, models, and data transformations, and QType handles the execution.

**Elevator pitch:** QType turns AI application prototypes from days of Python coding into hours of YAML configuration, without sacrificing maintainability or requiring you to learn yet another GUI tool.

---

## Core Mental Model: The Three Primitives

Understanding QType requires understanding three core concepts and how they relate:

**Think of QType like this:**

**Variables** are your data containers (typed boxes)  
**Steps** are your transformations (functions on boxes)  
**Flows** are your pipelines (sequences of transformations)  
**The DSL** is your specification language (what you write)  
**The Semantic layer** is your validator (what checks it)  
**The Interpreter** is your executor (what runs it)  

**You declare what you want, QType handles how to do it.**


### 1. Variables: The Data

**Variables are typed data containers** that hold values as they move through your application.

```yaml
variables:
  - id: question          # A variable named "question"
    type: text            # It holds text data
  - id: answer
    type: text
  - id: reviews
    type: list[text]      # Can hold complex types like lists
```

**Key insight:** Variables are *declared* upfront, making data flow explicit before runtime.

**Types matter:** Every variable has a type (primitive like `text`/`int`, domain-specific like `ChatMessage`, or custom types you define). 

---

### 2. Steps: The Transformations

**Steps are individual operations** that take input variables and produce output variables.

```yaml
steps:
  - id: format_prompt
    type: PromptTemplate
    template: "Answer this: {question}"
    inputs:
      - question      # Consumes the question variable
    outputs:
      - prompt        # Produces a prompt variable
```

**Each step:**
- Has a specific type (`PromptTemplate`, `LLMInference`, `InvokeTool`, etc.)
- Declares which variables it reads (`inputs`)
- Declares which variables it produces (`outputs`)
- Performs one focused transformation

**Key insight:** Steps are pure transformations. Everything is declared, making flows inspectable and debuggable.

**Step types are extensible:** QType ships with ~25 step types (LLMs, tools, data processing, RAG operations), and you can write custom tools for domain-specific operations.

---

### 3. Flows: The Orchestration

**Flows are sequences of steps** that form complete processing pipelines.

```yaml
flows:
  - id: answer_question
    inputs:
      - question          # What comes in
    outputs:
      - answer            # What goes out
    variables:            # All data containers
      - id: question
        type: text
      - id: prompt
        type: text
      - id: answer
        type: text
    steps:
      - id: format_prompt
        type: PromptTemplate
        # ... (transforms question → prompt)
      - id: get_answer
        type: LLMInference
        # ... (transforms prompt → answer)
```

**Flows are data pipelines:**
- They receive input variables
- Pass them through a sequence of steps
- Each step transforms data from one form to another
- Final outputs are extracted and returned

**Key insight:** Flows are *stateless* by default - each execution is independent. Use Memory or external storage for stateful applications (like chatbots). This makes flows easy to reason about, test, and parallelize.

---

## The Data Flow Model

Here's how data moves through a QType application:

```
Input Variables
     ↓
   Step 1 (transforms A → B)
     ↓
   Step 2 (transforms B → C)
     ↓
   Step 3 (transforms C → D)
     ↓
Output Variables
```

**Linear execution:** Steps run sequentially in declaration order. Each step waits for its inputs to be available. Parallelism is supported for multiple inputs.

**1-to-many cardinality:** Some steps (like `Explode`) can produce multiple outputs for one input, creating fan-out patterns. Other steps (like `Collect`) gather many inputs into one collection. This enables batch processing patterns.

---

## Architecture: The Three Layers

QType is built in three distinct layers, each with a specific responsibility:

```
┌─────────────────────────────────────────────┐
│              CLI Commands                   │ 
│         (validate, run, serve)              │
├─────────────────────────────────────────────┤
│             Interpreter                     │
│         (execution engine)                  │
├─────────────────────────────────────────────┤
│              Semantic                       │
│         (linking & validation)              │
├─────────────────────────────────────────────┤
│                DSL                          │
│          (core data models)                 │
└─────────────────────────────────────────────┘
```

### Layer 1: DSL (Domain-Specific Language)

**Responsibility:** Define the data structures that represent QType specifications.

- Pure Pydantic models
- No business logic, just structure
- Represents YAML as typed Python objects
- References are strings (like `model: "gpt-4"`)

**Example:** The `Flow` model has `steps: list[Step]`, `variables: list[Variable]`, etc.

---

### Layer 2: Semantic

**Responsibility:** Transform DSL objects into resolved, validated representations.

**The pipeline:**

1. **Parse** - Load YAML and build DSL objects
2. **Link** - Resolve string references to actual objects (`"gpt-4"` → `Model` object)
3. **Resolve** - Build semantic IR (intermediate representation) where all IDs become object references
4. **Check** - Validate semantic rules (no missing variables, types match, etc.)

**Key insight:** This layer catches errors *before* execution. You get fast feedback without running expensive LLM calls.

**Symbol table:** During linking, QType builds a map of all components by ID.

---

### Layer 3: Interpreter

**Responsibility:** Execute flows by running steps with real resources.

- Creates executors for each step type
- Manages resources (models, indexes, caches)
- Handles streaming and progress tracking
- Emits telemetry events
- Orchestrates async execution

**Executor pattern:** Each step type has an executor class (`LLMInferenceExecutor`, `InvokeToolExecutor`, etc.) that knows how to run that specific operation. Executors receive `ExecutorContext` with cross-cutting concerns like auth, telemetry, and progress tracking.

**Key insight:** The interpreter layer is optional - you could generate code from semantic IR, compile to a different runtime, or build alternative execution strategies. The DSL and semantic layers are independent of execution.

---

## The Loading Pipeline

When you run `qtype validate` or `qtype run`, here's what happens:

```
YAML File
    ↓
1. Load (expand env vars, includes)
    ↓
2. Parse (YAML → DSL models)
    ↓
3. Link (resolve ID references)
    ↓
4. Resolve (DSL → Semantic IR)
    ↓
5. Check (validate semantics)
    ↓
6. Execute (run the flow)
```
Each stage builds on the previous, and errors are caught as early as possible.

---

## Philosophy: Why QType Exists

### 1. **Code is a Liability**

Every line of Python code you write is something you have to maintain, debug, and explain to colleagues. QType shifts complexity from *imperative code* (how to do it) to *declarative specification* (what to do).

**Example:** Instead of writing Python to:
- Initialize an LLM client
- Format prompts
- Handle streaming
- Parse JSON responses
- Construct typed objects
- Log telemetry

You write YAML that *declares* these operations, and QType handles the implementation.

---

### 2. **Modularity and Composability**

QType applications are built from composable pieces:
- **Flows** can invoke other flows
- **Tools** are reusable functions
- **Types** define domain models
- **Models** and **Memories** are shared resources

You can build libraries of flows, tools, and types that work together like Lego blocks.

---

### 3. **Traceability and Observability**

Because everything is declared:
- You can visualize the entire application structure
- Trace data flow through the system
- Emit structured telemetry
- Understand what's happening without reading code

Otel Observability is supported by default.

QType makes the *implicit* (hidden in code) *explicit* (visible in YAML).

---

### 4. **Rapid Iteration**

Changing a QType application is fast:
- Edit YAML
- Validate
- Run

No recompiling, no virtual environment issues, no import errors. The feedback loop is seconds, not minutes.

---

## What QType Is NOT

### ❌ Not a Low-Code/No-Code Tool

QType is not Flowise, Dify, LangFlow, or similar GUI-based agent builders.

**Why not:**
- **Audience:** QType targets *engineers* who want text-based specifications they can version control, code review, and integrate into CI/CD
- **Control:** GUI tools trade precision and flexibility for convenience. QType gives you full control via explicit configuration, and can connect to apis or your code.
- **Complexity ceiling:** GUIs work great for simple flows but become unwieldy for complex applications with dozens of components. YAML scales better for large systems

**When to use GUI tools:** If you're non-technical or building simple demo flows, GUI tools are faster. If you're an engineer building prototype systems, QType is more maintainable.

---

### ❌ Not a General Data Engineering Tool

**What it is:** QType is not Dagster, Prefect, Airflow, or similar orchestration frameworks.

**Why not:**
- **Focus:** Data engineering tools excel at *data pipelines* (ETL, batch processing, scheduling). QType excels at *AI workflows* (LLM calls, vector search, tool calling, agents)
- **Features:** Dagster has sophisticated scheduling, retries, dependency management, and data lineage. QType has LLM abstractions, type systems for AI data (ChatMessage, RAGDocument), and streaming support
- **Overlap:** Both can process data in pipelines, but the primitives are different

**When to use data engineering tools:** If your workflow is primarily data transformation, aggregation, and movement without AI components, use Dagster/Airflow. They're better at traditional ETL.

**When to use QType:** If your workflow involves LLMs, embeddings, vector search, tool calling, or agents, QType gives you purpose-built primitives. You *could* build these in Dagster, but QType makes it easier.

**Can they coexist?** Yes! Use Dagster to orchestrate data pipelines that feed into QType applications, or use QType flows as Dagster ops for AI-specific processing.

---

## When to Use QType

### ✅ Use QType When:

**You're prototyping AI applications**
- Quickly try different LLMs, prompts, and flows
- Iterate on application structure without Python boilerplate
- Get validation feedback instantly

**You want type-safe AI workflows**
- Explicit data flow with typed variables
- Catch errors before runtime
- Understand what data flows where

**You're building modular AI systems**
- Reusable flows, tools, and types
- Compose applications from libraries
- Share components across projects

**You value maintainability**
- YAML specs are easier to review than Python
- Version control shows exactly what changed
- Generate documentation automatically

**You need observability**
- Built-in telemetry and tracing
- Visualize application structure
- Understand execution patterns

---

### 🤔 Consider Alternatives When:

**You need complete Python control**
- Complex branching logic
- Dynamic behavior based on runtime conditions
- Integration with Python-specific libraries

**You're building pure data pipelines**
- No LLM or AI components
- Traditional ETL operations
- Dagster/Airflow are better fits

**You prefer visual tools**
- GUI-based development
- Non-technical users
- Flowise/Dify are more appropriate

**Your workflow is extremely simple**
- Single LLM call, no orchestration
- Direct API usage is simpler
- QType adds unnecessary structure

