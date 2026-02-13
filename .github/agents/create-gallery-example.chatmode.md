---
description: Create a new example application for the QType documentation gallery
tools: ['vscode', 'execute', 'read', 'edit', 'search', 'web', 'agent', 'todo']
---

# Create Gallery Example

You are helping create example applications for the QType documentation gallery. Each gallery example provides users with an example reference of an AI application.

## File Structure

Each example requires two files:

1. **Documentation**: `docs/Gallery/{Category}/{name}.md`
2. **QType YAML**: `examples/{category}/{name}.qtype.yaml`

Where:
- `{Category}` is title case with spaces (e.g., "Conversational AI")
- `{category}` is lowercase with underscores (e.g., "conversational_ai")
- `{name}` is lowercase with underscores (e.g., "simple_chatbot")

## Example Categories

From DOCUMENTATION_ROADMAP.md:
- **Conversational AI**: Simple Chatbot, Multi-Turn Reasoning Agent, Customer Support Bot
- **RAG & Document Processing**: Complete RAG System, Semantic Search Q&A, Multi-Modal Document Analysis, Hybrid Search System
- **Data Processing**: ETL Pipeline, Batch Document Classification, Structured Data Extraction, CSV Processing at Scale
- **Multi-Agent Systems**: Research Assistant, Collaborative Agents
- **Specialized**: Evaluation & Judging, Content Moderation

## Workflow

### Step 1: Create QType YAML

Create the example application in `examples/{category}/{name}.qtype.yaml`:

**Minimalism is Critical**:
- Only include what's necessary to demonstrate the specific concept
- Don't add extra steps, types, or variables unless they're essential
- Keep the YAML as concise as possible while remaining functional
- If the example can work without a feature, remove it

**Reference Syntax**:
- **NEVER use `$ref` syntax** - QType uses simple string references by ID
- ✅ Correct: `model: nova` or `inputs: [user_message]`
- ❌ Wrong: `model: {$ref: nova}` or `inputs: [{$ref: user_message}]`
- References work by name lookup, not by JSON pointer

**Common Mistakes to Avoid**:
- Don't create custom types unless the example specifically demonstrates custom types
- Don't add collection/aggregation steps unless demonstrating data processing
- Don't add extra variables that aren't used in the example
- Don't include `type: Application` field (it's inferred)
- Don't over-comment - only add comments for non-obvious logic

**Best Practices**:
- Use AWS Bedrock as the default model provider (amazon.nova-lite-v1:0)
- Use domain types (ChatMessage, RAGSearchResult, etc.) when appropriate
- Keep inference_params minimal (temperature, max_tokens only when relevant)
- Use descriptive IDs that make the flow clear

### Step 2: Generate Mermaid Diagram

After the YAML is approved, run:
```bash
uv run qtype visualize -nd examples/{category}/{name}.qtype.yaml -o "docs/Gallery/{Category}/{name}.mermaid"
```

### Step 3: Create Documentation

Create `docs/Gallery/{Category}/{name}.md` following this exact structure:

```markdown
# {Example Name}

## Overview

{2-3 sentence description of what the example does and demonstrates}

## Architecture

--8<-- "Gallery/{Category}/{name}.mermaid"

## Complete Code

\`\`\`yaml
--8<-- "../examples/{category}/{name}.qtype.yaml"
\`\`\`

## Key Features

- **{Schema Object/Type}**: {What it does and how it works briefly}
- **{Schema Object/Type}**: {What it does and how it works briefly}
...

## Running the Example

\`\`\`bash
# Start the server (if applicable)
qtype serve examples/{category}/{name}.qtype.yaml

# Or run directly
qtype run examples/{category}/{name}.qtype.yaml
\`\`\`

## Learn More

- Tutorial: [Link to related tutorial](../../Tutorials/{tutorial}.md) {only if exists}
- How-To: [Link to related how-to](../../How-To%20Guides/{guide}.md) {only if exists}
- Example: [Link to related example](../../Gallery/{guide}.md) {only if exists}
```

## Critical Rules for Documentation

### Snippet Paths
- **Mermaid**: `"Gallery/{Category}/{name}.mermaid"` (relative to docs root)
- **YAML**: `"../examples/{category}/{name}.qtype.yaml"` (relative to docs root)
- Paths are NOT relative to the current .md file
- Do NOT use `./` or `../../../` patterns

### Key Features Section

**MUST BE**: Schema objects, types, parameters, or attributes defined in the QType DSL
- ✅ Good: "Conversational Interface", "Memory", "ChatMessage Type", "LLMInference Step", "system_message parameter"
- ❌ Bad: "Model Abstraction", "Type Safety", "Simple Architecture", "Declarative Step Definition"

**Process for writing feature descriptions**:
1. Dig into the codebase to understand the feature (use grep_search, read_file on qtype/dsl/, qtype/semantic/, qtype/interpreter/)
2. Read the model definitions, field descriptions, and executor implementations
3. Write a concise description that explains:
   - What the feature is (schema object, type, parameter)
   - What it does (its purpose/behavior)
   - How it works (mechanism/implementation detail)
4. Keep it brief (1 sentence, max 2)

### Example Key Features:

```markdown
- **Conversational Interface**: Flow interface type that automatically accumulates chat messages in `conversation_history` and passes them to LLM steps for context-aware responses
- **Memory**: Conversation history buffer with `token_limit` that stores messages and automatically flushes oldest content when limit is exceeded
- **ChatMessage Type**: Built-in domain type with `role` field (user/assistant/system) and `blocks` list for structured multi-modal content
- **LLMInference Step**: Executes model inference with optional `system_message` prepended to conversation and `memory` reference for persistent context across turns
- **Model Configuration**: Model resource with provider-specific `inference_params` including `temperature` (randomness) and `max_tokens` (response length limit)
```

## Links Section

Only link to documentation that already exists. Do NOT create placeholder links for:
- Tutorials that haven't been written
- How-To guides that don't exist
- Reference docs not yet created

Check the docs/ directory structure to verify files exist before linking.

## Commands Reference

```bash
# Validate the YAML
uv run qtype validate examples/{category}/{name}.qtype.yaml

# Test the application
uv run qtype run examples/{category}/{name}.qtype.yaml

# Generate visualization
uv run qtype visualize -nd examples/{category}/{name}.qtype.yaml -o "docs/Gallery/{Category}/{name}.mermaid"

# Serve the application
uv run qtype serve examples/{category}/{name}.qtype.yaml
```

## QType-Specific Guidelines

Follow all guidelines from `.github/copilot-instructions.md`:
- Use `uv run` for all commands
- Follow PEP8 and project style guidelines
- Use AWS Bedrock models by default
- Keep examples minimal and focused
- Include type hints where appropriate in comments
