# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

QType is a domain-specific language (DSL) for rapid prototyping of AI applications. It enables developers to define modular, composable AI systems using structured YAML-based specifications.

## Essential Commands

### Development Environment
```bash
# This is a uv project - all commands run inside virtual environment
uv run <command>

# Install dependencies (including dev dependencies)
uv sync
```

### Testing
```bash
# Run all tests
uv run pytest

# Run specific test file
uv run pytest tests/test_file.py

# Run tests with coverage
uv run pytest --cov=qtype --cov-report=html
```

### Linting & Type Checking
```bash
# Run ruff linter
uv run ruff check qtype/

# Run ruff formatter
uv run ruff format qtype/

# Run isort (import sorting)
uv run isort qtype/

# Run type checker (ty is used, not mypy)
uv run ty check
```

### CLI Commands
```bash
# Validate a QType spec
uv run qtype validate hello_world.qtype.yaml

# Serve a QType spec (launches web UI and API)
uv run qtype serve hello_world.qtype.yaml

# Serve with auto-reload on file changes
uv run qtype serve hello_world.qtype.yaml --reload

# Run a flow directly from CLI
uv run qtype run hello_world.qtype.yaml --flow chat_example --input '{"user_message": "hello"}'

# Visualize flow architecture
uv run qtype visualize hello_world.qtype.yaml --output diagram.png

# Start MCP server for Claude integration
uv run qtype mcp
```

## Architecture Overview

QType uses a **5-layer architecture** that transforms YAML specifications into executable AI applications:

```
Commands (CLI) → Application (API/UI) → Interpreter (execution) → Semantic (validation) → DSL (parsing)
```

### Layer 1: DSL Layer (`qtype/dsl/`)
**Purpose:** Parse YAML specifications into strongly-typed Python models

**Key files:**
- `model.py` - Core DSL type definitions (Application, Flow, Step, Variable, etc.)
- `parser.py` - Converts raw YAML dict into DSL models
- `linker.py` - Resolves string ID references (`$ref`) to actual object references
- `loader.py` - Low-level YAML file loading with env var substitution and file inclusion

**Important concepts:**
- Uses Pydantic with StrictBaseModel for strict validation
- References use `$ref` syntax in YAML (e.g., `model: {$ref: "gpt-4"}`)
- Optional types use `?` suffix (e.g., `text?`)
- List types use bracket syntax (e.g., `list[text]`)

### Layer 2: Semantic Layer (`qtype/semantic/`)
**Purpose:** Validate DSL models and resolve to immutable semantic intermediate representation (IR)

**Key files:**
- `model.py` - Semantic IR types (immutable versions of DSL models)
- `loader.py` - Main entry point that orchestrates full validation pipeline
- `resolver.py` - Converts DSL objects to semantic IR
- `checker.py` - Validates semantic rules (flow connectivity, type matching, etc.)

**Validation pipeline order:**
1. Load YAML → Raw dict (env vars, includes resolved)
2. Parse → DSL Application (Pydantic validation)
3. Link → Resolved DSL (ID references become object references)
4. Resolve to IR → Semantic Application (DSL → immutable IR)
5. Check Rules → Validated semantic IR (semantic constraints enforced)

### Layer 3: Interpreter Layer (`qtype/interpreter/`)
**Purpose:** Execute flows as streams of FlowMessage objects through chained StepExecutors

**Key files:**
- `flow.py` - Main entry point `run_flow()` that chains executors
- `base/base_step_executor.py` - Abstract base for all step executors
- `base/factory.py` - Creates appropriate executor instance based on step type
- `executors/` - 25+ step-specific executors (llm_inference, agent, vector_search, etc.)

**Execution model:**
- FlowMessage is an immutable capsule containing session, variables, and optional error
- Each step executor processes async stream of FlowMessages
- Failed messages skip processing and propagate through pipeline
- Executors can emit stream events for real-time UI updates

### Layer 4: Application Layer (`qtype/application/`)
**Purpose:** Generate REST APIs and web UI from semantic Application models

**Key files:**
- `interpreter/api.py` - Creates FastAPI app with dynamic endpoints from flows
- `interpreter/endpoints.py` - Generate REST routes for flows
- `interpreter/stream/chat/` - Converts FlowMessage streams to Vercel AI SDK format

### Layer 5: Commands Layer (`qtype/commands/`)
**Purpose:** CLI commands for development and deployment workflows

Each command file (validate.py, serve.py, run.py, etc.) implements a specific CLI command.

## Key Development Patterns

### Adding a New Step Type

When adding a new step type, follow these steps:

1. **Define DSL Model** in `dsl/model.py`:
   ```python
   class MyCustomStep(Step):
       type: Literal["MyCustomStep"] = "MyCustomStep"
       my_config: str = Field(...)
   ```

2. **Add to StepType Union** in `dsl/model.py`:
   ```python
   StepType = Annotated[Union[..., MyCustomStep], Field(discriminator="type")]
   ```

3. **Create Semantic IR** in `semantic/model.py`:
   ```python
   class MyCustomStep(ImmutableModel):
       # Same fields as DSL version
   ```

4. **Add to Resolver** in `semantic/resolver.py` (if complex resolution needed)

5. **Create Executor** in `interpreter/executors/my_executor.py`:
   ```python
   class MyCustomExecutor(StepExecutor):
       async def process_message(self, message: FlowMessage):
           # Process message and yield results
           yield result_message
   ```

6. **Register in Factory** in `interpreter/base/factory.py`:
   ```python
   EXECUTOR_REGISTRY[MyCustomStep] = "qtype.interpreter.executors.my_executor.MyCustomExecutor"
   ```

7. **Add Semantic Validation** in `semantic/checker.py`:
   ```python
   def _check_my_custom_step(step: MyCustomStep) -> None:
       # Validate semantic rules
   ```

### FlowMessage Propagation

Messages flow through the pipeline:
```
FlowMessage(variables={"input": "hello"})
  → Step1Executor.process_message()
  → FlowMessage(variables={"step1_out": "..."})
  → Step2Executor.process_message()
  → FlowMessage(variables={"output": "..."})
```

Failed messages skip processing:
```python
if message.is_failed():
    yield message  # Pass through unchanged
else:
    # Process message
```

### Reference Resolution

References are resolved at different stages:
- **DSL**: References as strings or `{$ref: "id"}` objects
- **Linking**: Strings converted to object references
- **Semantic**: All references resolved to actual objects
- **Execution**: Executors work with resolved objects only

## Critical Constraints

### Semantic Model Generation

⚠️ **NEVER manually edit `qtype/semantic/model.py`**

The semantic model is **auto-generated** from DSL models using:
```bash
uv run qtype generate semantic-model
```

**Why this matters:**
- `semantic/model.py` must stay in sync with `dsl/model.py`
- Manual edits will break `test_generate_semantic_model_matches_existing`
- Changes to semantic models should be made in DSL first, then regenerated

**If you need to add new semantic models:**
1. Add the model to `qtype/dsl/model.py` first
2. Run `uv run qtype generate semantic-model` to regenerate
3. Verify with `uv run pytest tests/semantic/test_semantic_generator.py`

**Exception:** Simple immutable wrappers and helper classes can be added manually, but discriminated union types and core models MUST be auto-generated.

### Span Injection and Tracing

When adding tracing/observability features:

**Prefer abstraction over direct modification:**
- Add span creation and metadata injection at the appropriate abstraction level
- For output-level spans, consider using the base executor pattern rather than modifying `flow.py` directly
- Think about where the feature belongs architecturally, not just what file is easiest to modify

**Best practices:**
- Create child spans for logical units of work
- Inject metadata (span_id, trace_id) into FlowMessage.metadata
- Set span attributes that are useful for debugging
- Handle cases where telemetry is not configured

### Testing Requirements

When implementing new features:

**Always run the full test suite before considering a feature "done":**
```bash
uv run pytest  # Run ALL tests, not just the ones you created
```

**Pay special attention to:**
- Integration tests that verify end-to-end behavior
- Tests that validate architectural patterns, not just functionality

**Test coverage should include:**
- Unit tests for new models and functions
- Integration tests for cross-layer functionality
- Negative tests for error conditions
- Mock-based tests for external integrations (Phoenix, LLM APIs, etc.)

## Python Code Guidelines

All Python code in this repository must follow strict guidelines defined in `.github/copilot-instructions.md`:

### Critical Import Rules
- When importing multiple items from the SAME module WITHOUT aliases: use comma-separated on ONE line
  - ✅ `from qtype.dsl.model import ListType, Variable, CustomType`
  - ❌ `from qtype.dsl.model import ListType` then `from qtype.dsl.model import Variable`
- When importing with aliases: use separate lines
  - ✅ `from qtype.semantic import checker` then `from qtype.semantic import model as ir`
  - ❌ `from qtype.semantic import checker, model as ir`

### Type Annotations
- Use Python 3.10+ built-in types (`list`, `dict`, not `List`, `Dict`)
- Use `|` for union types (`int | str` not `Union[int, str]`)
- Use `| None` for optional types (`str | None` not `Optional[str]`)
- Use `from __future__ import annotations` for forward references
- Always add type hints to all function parameters, return values, and class attributes

### Code Style
- Follow PEP8 with line length = 79 characters
- Use double quotes for strings
- Use f-strings for string interpolation
- Avoid unnecessary parentheses (e.g., `x = Path(__file__).parent / "file.txt"`)
- For long assert messages, put message in parentheses on next line

### Anti-patterns to Avoid
- Don't use `if TYPE_CHECKING` unless absolutely necessary
- Don't use try-then-raise pattern unless transforming exception type
- Avoid premature optimization - follow YAGNI principle
- Don't use `useMemo` or `useCallback` in React code

## Testing Patterns

- Tests live in `tests/` directory
- Test files follow `test_*.py` naming convention
- Use pytest fixtures for common setup
- Mark slow tests with `@pytest.mark.slow`
- Mark network tests with `@pytest.mark.network`
- Async tests use `@pytest.mark.asyncio` or rely on auto-detection

## Documentation

- Full documentation is built with MkDocs and lives in `docs/`
- Documentation includes tutorials, how-to guides, reference docs, and concepts
- Component documentation is auto-generated from Pydantic models
- Build docs with: `uv run mkdocs serve`

## MCP Server

QType includes an MCP server for Claude integration:
- Located in `qtype/mcp/server.py`
- Exposes QType capabilities (validation, examples, documentation search) as MCP resources
- Start with: `uv run qtype mcp`

## Key Files to Understand

For rapid understanding of the codebase:
1. `qtype/cli.py` - Main CLI entry point
2. `qtype/dsl/model.py` - All DSL type definitions
3. `qtype/semantic/loader.py` - Validation pipeline orchestrator
4. `qtype/interpreter/flow.py` - Flow execution entry point
5. `qtype/interpreter/base/base_step_executor.py` - Executor base class
6. `qtype/interpreter/base/factory.py` - Executor registry and factory

## Environment Variables

Create a `.env` file for API keys and configuration:
```
OPENAI_API_KEY=sk-...
AWS_REGION=us-east-1
# Add other API keys as needed
```

Variables are automatically loaded and can be referenced in YAML specs with `${VAR_NAME}` syntax.
