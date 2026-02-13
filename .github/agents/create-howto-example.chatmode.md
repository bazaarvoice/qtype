---
description: Create a new How-To guide for the QType documentation
tools: ['vscode', 'execute', 'read', 'edit', 'search', 'web', 'agent', 'todo']
---

# Create How-To Guide

You are helping create How-To guides for QType documentation. Each How-To provides a focused, task-oriented solution to a specific problem.

## File Structure

Each How-To requires one file:

**Documentation**: `docs/How To/{Category}/{name}.md`

Where:
- `{Category}` is title case with spaces (e.g., "Data Processing")
- `{name}` is lowercase with underscores (e.g., "adjust_concurrency")

## How-To Categories

From DOCUMENTATION_ROADMAP.md:

- **Language Features**: Environment variables, references, includes, list types, session inputs
- **Command Line Usage**: CLI inputs, file loading
- **Data Processing**: SQL, files (CSV/JSON/text), documents, fan-out, aggregation, debugging
- **Invoke Models**: Prompts, LLMs, embeddings, model parameters, memory, provider switching
- **Authentication**: API keys, bearer tokens, OAuth2, AWS, Google Vertex, secret management
- **Observability & Debugging**: Validation, visualization, Phoenix, Langfuse, OpenTelemetry
- **Data & Types**: Built-in types, domain types, custom types, FieldExtractor, Construct
- **Tools & Integration**: OpenAPI specifications, Python modules, tool bindings
- **Retrieval Augmented Generation (RAG)**: Document conversion, chunking, embedding, vector/document indexes, search, filtering, reranking
- **Conversational Interfaces**: Flow interfaces, memory, conversation history, session persistence
- **Interfaces**: HTTP API, serve, interactive UI, variable UI hints
- **Extension & Advanced**: CLI plugins, step caching, custom step types

## How-To Structure

```markdown
# {Task as Question}

{1-2 sentence overview of the problem / approach}

### QType YAML

\`\`\`yaml
# Only the relevant YAML snippet, not complete app
{minimal snippet demonstrating the solution}
\`\`\`

### Explanation

- **{Schema Object/Type/Parameter}**: {1 line what it does}
- **{Schema Object/Type/Parameter}**: {1 line what it does}
- **{Schema Object/Type/Parameter}**: {1 line what it does}

## Complete Example

\`\`\`yaml
# Optional: include only if a full working example adds value
# Otherwise, omit this section entirely
# ALWAYS use snippet syntax to include from examples/ directory:
--8<-- "../examples/{category}/{example_name}.qtype.yaml"
\`\`\`

## See Also

- [Related How-To](../{Category}/{guide}.md)
- [Component Reference](../../components/{Component}.md)
- [Tutorial](../../Tutorials/{tutorial}.md)
- [Example](../../Gallery/{Category}/{example}.md)
```

## Critical Design Principles

### Brevity Over Completeness
- **How-Tos are NOT tutorials** - they solve one specific problem
- Show ONLY the relevant snippet, not a complete application
- If the snippet is 5-10 lines, that's perfect
- Omit `application:`, `flows:`, etc. unless directly relevant
- Focus on the configuration that answers the question

### Question-Oriented Titles
- ✅ "Add Vector Search to an Application"
- ✅ "Configure Chunking Strategies"
- ✅ "Rerank Search Results"
- ❌ "Vector Search" (too broad)
- ❌ "How to Use Chunking" (redundant "How to")

### Minimal Explanation
- Use bullet points only
- Each bullet: **{Thing}**: {What it does in 1 line}
- No prose paragraphs
- No architecture discussions
- Just enough to understand the snippet

### Complete Example = Optional
- Only include if the snippet alone isn't self-contained
- Must be a minimal, runnable YAML file stored in `examples/` directory
- ALWAYS use snippet syntax `--8<-- "../examples/{path}"` to include the file
- Create example files in appropriate subdirectories (e.g., `examples/language_features/`, `examples/data_processing/`)
- Prefer referencing existing examples in Gallery instead of creating new ones

## Workfl0: Create Example Files (if needed)

If a Complete Example section is needed:
1. Create working example in `examples/{category}/` directory
2. Validate with `uv run qtype validate examples/{category}/{name}.qtype.yaml` (Copilot execution)
3. Test with `uv run qtype run examples/{category}/{name}.qtype.yaml` (Copilot execution)
4. Use snippet syntax in documentation to include the file
5. **Important**: In the documentation itself, show commands as `qtype ...` (without `uv run`)

### Step ow

### Step 1: Understand the Task

Identify:
- What specific problem does this solve?
- What's the minimal configuration needed?
- What schema objects/types/parameters are involved?

### Step 2: Create Minimal Snippet

Extract ONLY the relevant portion:
- If showing a step configuration, show just that step
- If showing model configuration, show just the model resource
- If showing authentication, show just the auth_providers section
- Comment only non-obvious parts

**Reference Syntax**:
- **NEVER use `$ref` syntax** - QType uses simple string references by ID
- ✅ Correct: `model: nova` or `inputs: [user_message]`
- ❌ Wrong: `model: {$ref: nova}` or `inputs: [{$ref: user_message}]`

### Step 3: Research Schema Objects

For the Explanation section:
1. Use grep_search, read_file on qtype/dsl/, qtype/semantic/, qtype/interpreter/
2. Read model definitions, field descriptions, executor implementations
3. Write concise bullets explaining:
   - What each schema object/parameter is
   - What it does (purpose/behavior)
   - How it works (mechanism)

### Step 4: AInclude Raw Text from Other Files"

```markdown
# Include Raw Text from Other Files

Load external text files into your YAML configuration using the `!include_raw` directive, useful for keeping prompts, templates, and long text content in separate files.

### QType YAML

\`\`\`yaml
steps:
  - id: generate_story
    type: PromptTemplate
    template: !include_raw story_prompt.txt
    inputs:
      - theme
      - tone
    outputs:
      - story
\`\`\`

**story_prompt.txt:**
\`\`\`txt
--8<-- "../examples/language_features/story_prompt.txt"
\`\`\`

### Explanation

- **!include_raw**: YAML tag that loads the contents of an external file as a raw string
- **Relative paths**: File paths are resolved relative to the YAML file's location
- **Template substitution**: The loaded text can contain variable placeholders (e.g., `{theme}`, `{tone}`) that are substituted at runtime
- **Use cases**just Concurrency" (snippet-only, no complete example)

```markdown
# Adjust Concurrency

Control parallel execution of steps to optimize throughput and resource usage using the `concurrency` parameter on steps that implement `ConcurrentStepMixin` or `BatchableStepMixin`.

### QType YAML

\`\`\`yaml
steps:
  - type: LLMInference
    id: classify
    model: nova
    concurrency: 10              # Process up to 10 items in parallel
    inputs: [document]
    prompt: "Classify this document: {{document}}"
\`\`\`

### Explanation

- **concurrency**: Maximum number of concurrent executions for this step (default: 5)
- **ConcurrentStepMixin**: Steps that can process multiple items in parallel (LLMInference, InvokeTool, VectorSearch)
- **BatchableStepMixin**: Steps that can batch API calls for efficiency (InvokeEmbedding, IndexUpsert)

## See Also

- [LLMInference Reference](../../components/LLMInference.md)
- [Example: Data Processing Pipeline](../../Gallery/Data%20Processing/batch_classification
  - type: VectorIndex
    id: doc_index
    embedding_model: titan_embed
    dimension: 1024

steps:
  - type: VectorSearch
    id: search
    index: doc_index
    inputs: [query]
    top_k: 5                     # Return top 5 results
    score_threshold: 0.7         # Minimum similarity score
\`\`\`

### Explanation

- **VectorIndex**: In-memory vector store with HNSW algorithm for similarity search
- **embedding_model**: EmbeddingModel resource used to generate query embeddings
- **dimension**: Vector dimension, must match embedding model output
- **top_k**: Number of results to return, ranked by similarity score
- **score_threshold**: Minimum cosine similarity (0-1) for results

## See Also

- [VectorIndex Reference](../../components/VectorIndex.md)
- [VectorSearch Reference](../../components/VectorSearch.md)
- [Example: RAG System](../../Gallery/RAG%20%26%20Document%20Processing/rag_system.md)
```

## Commands Reference

**In Documentation** (user-facing):
```bash
# Validate snippet syntax (if creating complete example)
qtype validate examples/howto/{name}.qtype.yaml

# Test complete example
qtype run examples/howto/{name}.qtype.yaml
```

**For Copilot Execution** (actual terminal commands must use `uv run`):
```bash
# Copilot must prefix all qtype commands with 'uv run'
uv run qtype validate examples/howto/{name}.qtype.yaml
uv run qtype run examples/howto/{name}.qtype.yaml
```

## QType-Specific Guidelines

Follow all guidelines from `.github/copilot-instructions.md`:
- Use `uv run` for all commands
- Follow PEP8 and project style guidelines
- Use AWS Bedrock models by default in examples
- Keep snippets minimal and focused
- Reference existing schema objects accurately
