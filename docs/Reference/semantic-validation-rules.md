# Semantic Validation Rules

Semantic validation happens after loading your yaml. You should expect to see these even if the yaml is validated by the spec.

You can validate any qtype file with:
```
qtype validate you_file.qtype.yaml
```

This document lists all semantic validation rules enforced by QType. These rules are checked after YAML parsing and reference resolution.

---

## Agent

- Must have exactly 1 input
- Must have exactly 1 output
- Input must be type `text` or `ChatMessage`
- Output type must match input type

---

## Application

- If using `SecretReference`, must configure `secret_manager`
- For `AWSSecretManager`, auth must be `AWSAuthProvider`

---

## AWSAuthProvider

- Must specify at least one authentication method:
  - Access keys (`access_key_id` + `secret_access_key`)
  - Profile name (`profile_name`)
  - Role ARN (`role_arn`)
- If assuming a role, must provide base credentials (access keys or profile)

---

## BedrockReranker

- Must have exactly 2 inputs
- One input must be type `text` (query)
- One input must be type `list[SearchResult]` (results to rerank)
- Must have exactly 1 output of type `list[SearchResult]`

---

## Collect

- Must have exactly 1 input -- any type `T`
- Must have exactly 1 output of type `list[T]`
- Output list element type must match input type

---

## Construct

- Must have at least 1 input
- Must have exactly 1 output
- Output type must be a Pydantic BaseModel (Custom type or Domain type)

---

## Decoder

- Must have exactly 1 input of type `text`
- Must have at least 1 output

---

## DocToTextConverter

- Must have exactly 1 input of type `RAGDocument`
- Must have exactly 1 output of type `RAGDocument`

---

## DocumentEmbedder

- Must have exactly 1 input of type `RAGChunk`
- Must have exactly 1 output of type `RAGChunk`

---

## DocumentSearch

- Must have exactly 1 input of type `text`
- Must have exactly 1 output of type `list[SearchResult]`

---

## DocumentSource

- Must have exactly 1 output of type `RAGDocument`

---

## DocumentSplitter

- Must have exactly 1 input of type `RAGDocument`
- Must have exactly 1 output of type `RAGChunk`

---

## Echo

- Input and output variable IDs must match (order can differ)

---

## Explode

- Must have exactly 1 input of type `list[T]`
- Must have exactly 1 output of type `T`
- Output type must match input list element type

---

## FieldExtractor

- Must have exactly 1 input
- Must have exactly 1 output
- `json_path` must be non-empty

---

## Flow

**General:**
- Must have at least 1 step
- All step inputs must be fulfilled by flow inputs or previous step outputs

**Conversational Interface:**
- Must have exactly 1 `ChatMessage` input
- All non-ChatMessage inputs must be listed in `session_inputs`
- Must have exactly 1 `ChatMessage` output

**Complete Interface:**
- Must have exactly 1 input of type `text`
- Must have exactly 1 output of type `text`

---

## IndexUpsert

**For Vector Index:**
- Must have exactly 1 input
- Input must be type `RAGChunk` or `RAGDocument`

**For Document Index:**
- Must have at least 1 input

---

## LLMInference

- Must have exactly 1 output
- Output must be type `text` or `ChatMessage`

---

## PromptTemplate

- Must have exactly 1 output
- Output must be type `text`

---

## SQLSource

- Must have at least 1 output

---

## VectorSearch

- Must have exactly 1 input of type `text`
- Must have exactly 1 output of type `list[RAGSearchResult]`

## See Also

- [Validate QType YAML](../How%20To/Observability%20%26%20Debugging/validate_qtype_yaml.md)
- [CLI Reference](cli.md)