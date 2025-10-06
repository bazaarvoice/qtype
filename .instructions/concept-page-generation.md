# QType Concept Page Generation Instructions

This document contains comprehensive instructions for generating concept pages for the QType documentation system. These instructions are based on the successful creation of `model.md`, `memory.md`, and `flow.md` concept pages.

## Overview

Concept pages document the core cognitive ideas and components of the QType system. They are located in `docs/Concepts/` and follow a consistent structure that balances conceptual understanding with practical implementation details.

## Required Structure

Each concept page MUST include the following sections in order:

### 1. Title and Cognitive Description
- Start with a level 1 heading using the concept name
- Provide 2-3 paragraphs explaining the cognitive idea behind the concept
- Explain what role it plays in the overall QType system
- Describe how it relates to or enables other concepts
- Focus on the "why" and "what" before diving into technical details

### 2. Rules and Behaviors Section
Document validation rules, restrictions, and automatic behaviors that occur in the semantic resolution or dsl validation.

This may include, but is not limited to:
- **Unique ID requirements** - All components need unique IDs within their scope
- **Required vs optional fields** - What fields are mandatory
- **Default value behaviors** - What happens when fields aren't specified
- **Automatic inference** - How the system automatically sets values (e.g., Flow input/output inference)
- **Validation errors** - What specific errors can occur and when
- **Semantic resolution behaviors** - Special handling during DSL to semantic conversion
- **Reference capabilities** - How the component can reference or be referenced by others

### 3. Core Component Section
- Include the main component snippet using: `--8<-- "components/ComponentName.md"`
- If there are specialized variants (like EmbeddingModel for Model), include them as subsections
- Use descriptive section titles like "Model Types" or "Specialized Variants"

### 4. Related Concepts Section (when applicable)
- Link to other concepts that this component directly depends on or collaborates with
- Use markdown links in the format: `[ConceptName](concept-filename.md)`
- Keep descriptions brief - just mention the relationship
- Avoid including component snippets for concepts that will have their own pages

### 5. Example Usage Section
Provide comprehensive YAML examples that demonstrate:
- **Basic usage** - Simple, straightforward example
- **Advanced configurations** - More complex scenarios
- **Real-world patterns** - Examples that users would actually implement
- **Integration examples** - How it works with other concepts

Examples should:
- Be complete and valid YAML following the spec in schema/qtype.schema.json
- Include realistic IDs and values
- Show progression from simple to complex
- Demonstrate the rules and behaviors described earlier
- Use consistent naming conventions

## Research Process

Before writing a concept page, gather information from:

1. **DSL Model Definition** (`qtype/dsl/model.py`)
   - Find the main class definition
   - Note field types, defaults, and descriptions
   - Look for validation decorators and special behaviors
   - Identify inheritance relationships

2. **Component Documentation** (`docs/components/ComponentName.md`)
   - Use for the core component snippet inclusion
   - Check for field descriptions and requirements

3. **Semantic Model** (`qtype/semantic/model.py`)
   - Look for differences from DSL version
   - Note any additional behaviors or constraints

4. **Validator Logic** (`qtype/dsl/validator.py`)
   - Search for component-specific validation rules
   - Look for automatic behavior implementations
   - Find error conditions and validation logic

5. **Examples** (`examples/` directory)
   - Look for existing usage patterns
   - Extract realistic configuration examples

6. **Generate Script** (`qtype/semantic/generate.py`)
   - Check for special handling in semantic generation
   - Look for type transformation rules

## Content Guidelines

### Tone and Style
- Use clear, accessible language
- Explain technical concepts in plain English
- Be prescriptive about best practices
- Focus on practical implementation

### Technical Accuracy
- All YAML examples must be syntactically correct
- Field types and requirements must match the actual implementation
- Validation rules must accurately reflect the codebase
- Default values must be correct

### Structure Consistency
- Use the same section headings across all concept pages
- Maintain consistent formatting for field descriptions
- Use similar example progression (basic → advanced)
- Keep related concepts section format consistent

## Example Patterns Observed

### Successful Patterns from Created Pages

**Model Concept:**
- Started with AI model configuration explanation
- Covered unique IDs, model ID resolution, provider requirements
- Included EmbeddingModel as specialized type
- Showed basic config, embedded config, and embedding examples
- Linked to AuthorizationProvider concept

**Memory Concept:**
- Explained persistent storage for conversation context
- Covered token management, chat history ratios, automatic flushing
- Showed basic memory, embedded memory, agent with memory, and multi-step examples
- Linked to LLMInference and Agent concepts

**Flow Concept:**
- Described orchestration mechanism for chaining steps
- Covered input/output inference, step requirements, sequential execution
- Provided sequential flow, conditional logic, nested flows, tool integration examples
- Referenced Step concept without including snippets (as requested)

### Component Inclusion Rules

- **Include snippets** for components that are exclusive to the concept or specialized variants
- **Link to concepts** for components that will have their own concept pages
- **Embed inline** for supporting types that won't get their own pages

## File Naming and Location

- Files go in: `docs/Concepts/`
- Filename format: `concept-name.md` (lowercase, hyphenated)
- Use the exact component name for the title (e.g., "Model", "Memory", "Flow")

## Quality Checklist

Before considering a concept page complete:

- [ ] All 5 required sections are present and properly ordered
- [ ] Cognitive description explains the "why" and "what"
- [ ] Rules and behaviors are comprehensive and accurate
- [ ] Component snippets are properly included
- [ ] Related concepts are appropriately linked
- [ ] Examples progress from simple to complex
- [ ] All YAML is valid and realistic
- [ ] Technical details match the implementation
- [ ] Writing is clear and accessible
- [ ] Formatting is consistent with existing pages

## Common Pitfalls to Avoid

1. **Don't include component snippets for concepts that will have their own pages** - Link instead
2. **Don't skip the cognitive explanation** - Always start with the conceptual understanding
3. **Don't provide incomplete examples** - YAML must be complete and valid
4. **Don't ignore validation rules** - Document all automatic behaviors and restrictions
5. **Don't use placeholder values** - Examples should be realistic and usable
6. **Don't forget edge cases** - Include examples of complex scenarios
7. **Don't mix up DSL vs semantic behaviors** - Clearly distinguish when necessary

## Future Concept Candidates

Based on the codebase structure, likely future concept pages include:
- Step (base class for all executable components)
- Tool (base for external operations)
- Agent (LLM with tools)
- AuthorizationProvider (authentication configuration)
- Index (searchable data structures)
- Application (top-level container)
- Variable (input/output definitions)

Each would follow the same structure and research process outlined above.