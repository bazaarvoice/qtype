# Create Embeddings

Generate vector embeddings from text using an embedding model, useful for semantic search, similarity comparisons, and RAG applications.

### QType YAML

```yaml
models:
  - type: EmbeddingModel
    id: titan_embed
    provider: aws-bedrock
    model_id: amazon.titan-embed-text-v2:0
    dimensions: 1024

flows:
  - type: Flow
    id: main
    steps:
      - type: InvokeEmbedding
        id: embed_text
        model: titan_embed
        inputs: [text]
        outputs: [embedding]
```

### Explanation

- **EmbeddingModel**: Defines an embedding model configuration with provider and dimensions
- **dimensions**: Size of the embedding vector (must match model output, e.g., 1024 for Titan v2)
- **InvokeEmbedding**: Step type that generates embeddings from input text
- **Embedding**: Output type containing the vector array and metadata

## Complete Example

```yaml
--8<-- "../examples/invoke_models/create_embeddings.qtype.yaml"
```

Run with:
```bash
qtype run examples/invoke_models/create_embeddings.qtype.yaml \
  -i '{"text": "Your text here"}'
```

## See Also

- [InvokeEmbedding Reference](../../components/InvokeEmbedding.md)
- [EmbeddingModel Reference](../../components/EmbeddingModel.md)
- [Tutorial: Build a RAG System](../../Tutorials/building_rag_system.md)
