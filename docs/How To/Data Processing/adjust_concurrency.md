# Adjust Concurrency

Control parallel execution of steps to optimize throughput and resource usage using the `concurrency_config` parameter on steps that support concurrent processing.

### QType YAML

```yaml
steps:
  - type: LLMInference
    id: classify
    model: nova
    concurrency_config:
      num_workers: 10         # Process up to 10 items in parallel
    inputs: [document]
    outputs: [classification]
```

### Explanation

- **concurrency_config**: Configuration object for concurrent processing with `num_workers` parameter
- **num_workers**: Maximum number of concurrent async workers for this step (default: 1)

### Steps Supporting Concurrency

The following step types support `concurrency_config`:

- **LLMInference**: Parallel LLM inference calls
- **InvokeEmbedding**: Parallel embedding generation
- **InvokeTool**: Parallel tool invocations
- **DocToTextConverter**: Parallel document conversion
- **DocumentSplitter**: Parallel document chunking
- **DocumentEmbedder**: Parallel chunk embedding
- **DocumentSearch**: Parallel search queries
- **BedrockReranker**: Parallel reranking operations

## See Also

- [Step Reference](../../components/Step.md)
- [Cache Step Results](cache_step_results.md)
- [Gallery: Dataflow Pipelines](../../Gallery/dataflow_pipelines.md)
