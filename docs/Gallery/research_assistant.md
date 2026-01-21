# Research Assistant

## Overview

A minimal “web research assistant” that takes a single input topic, searches the
web using Tavily, and then synthesizes an answer with an LLM call. This example
demonstrates how to reuse OpenAPI-generated tools via `references` and bind tool
outputs into an LLM prompt.

## Architecture

```mermaid
--8<-- "Gallery/research_assistant.mermaid"
```

## Complete Code

```yaml
--8<-- "../examples/research_assistant/research_assistant.qtype.yaml"
```

## Key Features

- **`references` (Application)**: Imports external QType documents (here, the Tavily
  tool library) so you can reference tools like `search` by ID
- **`BearerTokenAuthProvider.token`**: Stores the Tavily API key as a bearer token,
  loaded via `${TAVILY-API_BEARER}` environment-variable substitution
- **APITool**: Represents the Tavily HTTP endpoints (like `/search`) as typed tools
  with declared `inputs` and `outputs`
- **InvokeTool Step**: Calls the `search` tool and maps flow variables to tool
  parameters via `input_bindings`/`output_bindings`
- **PromptTemplate Step**: Builds the synthesis prompt by combining the user topic
  and the Tavily search results
- **LLMInference Step**: Produces the final `answer` by running model inference
  using the prompt produced by `PromptTemplate`

## Running the Example

### 1) Create a Tavily account + API key

Create an account at Tavily and generate an API key.

### 2) Set the Tavily token in a `.env`

Create a `.env` file next to `examples/research_assistant/research_assistant.qtype.yaml`:

```bash
TAVILY-API_BEARER=tvly-...
```

QType automatically loads a `.env` file from the spec’s directory when you run
`qtype run`.

### 3) Run

```bash
# Validate the YAML
qtype validate examples/research_assistant/research_assistant.qtype.yaml

# Run directly
qtype run -i '{"topic":"Latest developments in retrieval augmented generation"}' \
  examples/research_assistant/research_assistant.qtype.yaml
```

### Example Output

When running with the topic "Latest developments in retrieval augmented generation", the research assistant produces:

> #### Latest Developments in Retrieval-Augmented Generation
>
> Retrieval-Augmented Generation (RAG) has seen significant advancements, particularly in enhancing the accuracy and
> factual grounding of AI-generated content. Recent developments focus on improving the retrieval–generation
> pipeline, reducing hallucinations, and increasing performance metrics. For instance, performance improvements from
> 68% to 73% have been reported, with notable reductions in hallucinations and stronger factual grounding.
>
> Key areas of progress include:
>
> - **Enhanced Retrieval Mechanisms:** Improved algorithms for retrieving relevant information from large datasets.
> - **Stronger Factual Grounding:** Techniques that ensure generated content is more accurate and grounded in factual
> data.
> - **Reduction of Hallucinations:** Methods to minimize the generation of incorrect or misleading information.
> - **Targeted Enhancements:** Specific improvements across different stages of the retrieval–generation process.
>
> These advancements are expected to have a substantial impact on various applications, including natural language
> processing, content creation, and information retrieval systems.
>
> **Sources:**
>
> - [Latest Developments in Retrieval-Augmented Generation - CelerData](https://celerdata.com/glossary/latest-developments-in-retrieval-augmented-generation)
> - [Advancements in RAG [Retrieval-Augmented Generation] Systems by Mid-2025](https://medium.com/@martinagrafsvw25/advancements-in-rag-retrieval-augmented-generation-systems-by-mid-2025-935a39c15ae9)
> - [Retrieval-Augmented Generation: A Comprehensive Survey - arXiv](https://arxiv.org/html/2506.00054v1)

## Learn More

- How-To: [Create Tools from OpenAPI Specifications](../How%20To/Tools%20%26%20Integration/create_tools_from_openapi_specifications.md)
- How-To: [Bind Tool Inputs and Outputs](../How%20To/Tools%20%26%20Integration/bind_tool_inputs_and_outputs.md)
- How-To: [Include QType YAML](../How%20To/Language%20Features/include_qtype_yaml.md)
- How-To: [Call Large Language Models](../How%20To/Invoke%20Models/call_large_language_models.md)
