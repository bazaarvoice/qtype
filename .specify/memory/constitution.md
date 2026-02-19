<!--
Sync Impact Report
===================
Version change: N/A → 1.0.0
Modified principles: N/A (initial ratification)
Added sections:
  - Core Principles (5 principles)
  - Technology Stack & Standards
  - Development Workflow
  - Governance
Removed sections: N/A
Templates requiring updates:
  - .specify/templates/plan-template.md ✅ no changes needed
    (Constitution Check section is dynamically filled at plan time)
  - .specify/templates/spec-template.md ✅ no changes needed
    (generic template, no constitution-specific references)
  - .specify/templates/tasks-template.md ✅ no changes needed
    (generic template, no constitution-specific references)
  - .specify/templates/commands/ ✅ no command files present
Follow-up TODOs: none
-->

# QType Constitution

## Core Principles

### I. Code Quality

All code MUST pass the project's automated quality gates before
merge. This is non-negotiable.

- Every function, class, and module MUST have type hints and
  docstrings.
- All Python code MUST pass `ruff`, `ty`, and `isort` checks with
  zero violations.
- Logging MUST be used instead of print statements for all
  debug, info, and error output.
- Catch specific exceptions — bare `except` clauses are forbidden.
- Tests MUST accompany new functionality; untested code is
  incomplete code.

**Rationale**: Automated enforcement eliminates style debates and
catches defects early. Consistent quality makes the codebase
navigable by any contributor.

### II. Clean Design Patterns & Abstractions

Architecture MUST follow the established layered dependency flow:
CLI → Application → Interpreter → Semantic → DSL → Base.

- Each layer MUST only import from layers below it; never upward
  or sideways.
- Classes and functions MUST have a single, clear responsibility.
- Use composition over inheritance; prefer small, focused
  interfaces.
- Data structures MUST use Pydantic `BaseModel` for validation
  and serialization.
- Shared utilities belong in the Base layer; domain logic belongs
  in its respective layer.

**Rationale**: Strict layering prevents entanglement and makes each
component independently testable and replaceable.

### III. Concise, Minimal & Readable Code

Code MUST communicate intent clearly with the least amount of
syntax necessary.

- Prefer explicit over implicit — but never verbose over concise.
- Use f-strings, comprehensions, and pattern matching where they
  improve clarity.
- Lines MUST NOT exceed 79 characters unless breaking would harm
  readability.
- Functions SHOULD fit on a single screen (~30 lines); extract
  when they grow beyond that.
- Comments MUST explain *why*, not *what* — the code itself MUST
  explain the what.
- Remove dead code immediately; do not comment it out.

**Rationale**: Code is read far more often than it is written.
Minimalism reduces cognitive load and accelerates onboarding.

### IV. Async-First Execution

All I/O-bound operations MUST use asynchronous execution via
`async`/`await`.

- Network calls, file I/O, and external process invocations MUST
  be async.
- Use `asyncio` primitives (`gather`, `TaskGroup`, semaphores)
  for concurrency control.
- CPU-bound work SHOULD remain synchronous unless it blocks an
  event loop, in which case offload to a thread/process executor.
- Async functions MUST NOT call blocking synchronous I/O without
  wrapping in `asyncio.to_thread`.
- Prefer structured concurrency (`TaskGroup`) over bare
  `create_task` for proper error propagation.

**Rationale**: QType orchestrates LLM calls, tool invocations, and
document retrieval — all inherently I/O-bound. Async execution
maximizes throughput without thread complexity.

### V. Simplicity — YAGNI, DRY, No Over-Engineering

Build only what is needed *right now*. Eliminate duplication.
Resist speculative abstractions.

- Do NOT add code, parameters, or abstractions for hypothetical
  future requirements (YAGNI).
- Extract shared logic into a single source of truth when it
  appears in two or more places (DRY).
- Prefer flat, straightforward control flow over clever patterns.
- Optimization MUST be driven by measured bottlenecks, never by
  assumption.
- If a simpler solution solves the problem, it is the correct
  solution — complexity MUST be justified.

**Rationale**: Over-engineering is the leading cause of
unmaintainable code. Simplicity keeps velocity high and defect
rates low.

## Technology Stack & Standards

- **Language**: Python 3.10 — use all 3.10 features (union `|`
  types, `match`/`case`, built-in generics).
- **Package manager**: `uv` — all commands run via `uv run`.
- **Linting**: `ruff` (line-length 79, target py310).
- **Type checking**: `ty` with strict annotations.
- **Import sorting**: `isort` with standard/third-party/local
  grouping.
- **Data models**: Pydantic `BaseModel` for all structured data.
- **UI framework**: React + TypeScript with shadcn component
  library (functional components, hooks only).
- **Testing**: `pytest` via `uv run pytest`.

## Development Workflow

- All changes MUST be validated against `ruff`, `ty`, and `isort`
  before committing.
- Use feature branches; merge only after CI passes.
- Code review MUST verify adherence to these principles.
- Follow the project's copilot-instructions for detailed style
  rules (`.github/copilot-instructions.md`).
- Use `logging` for runtime diagnostics; structured logs
  preferred.

## Governance

This constitution is the authoritative source of engineering
standards for QType. It supersedes informal conventions and
personal preferences.

- **Amendments** require documentation of the change, rationale,
  and a version bump to this file.
- **Versioning** follows semantic versioning:
  - MAJOR: principle removal or incompatible redefinition.
  - MINOR: new principle or materially expanded guidance.
  - PATCH: clarifications, wording, or typo fixes.
- **Compliance** is verified during code review; every PR MUST
  be checked against these principles.
- **Complexity justification**: any deviation from Principle V
  MUST be documented inline with a rationale.

**Version**: 1.0.0 | **Ratified**: 2026-02-13 | **Last Amended**: 2026-02-13
