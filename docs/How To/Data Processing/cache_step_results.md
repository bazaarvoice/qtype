# Cache Step Results

Avoid redundant computation by caching step results on disk, enabling faster re-runs when processing the same inputs.

### QType YAML

```yaml
steps:
  - type: LLMInference
    id: classify
    model: nova
    inputs: [prompt]
    outputs: [category]
    cache_config:
      namespace: document_classification  # Logical grouping for cached data
      version: "1.0"                       # Change to invalidate cache
      on_error: Drop                       # Don't cache errors (default)
      ttl: 3600                            # Cache for 1 hour (seconds)
      compress: false                      # Optionally compress cached data
```

### Explanation

- **cache_config**: Enables step-level caching with configuration options
- **namespace**: Logical separation for cache entries (e.g., different projects or data domains)
- **version**: Cache version string - increment to invalidate all cached results for this step
- **on_error**: How to handle errors - `Drop` (don't cache errors, default) or `Cache` (cache error results)
- **ttl**: Time-to-live in seconds before cached entries expire
- **compress**: Whether to compress cached data (saves disk space, adds CPU overhead)

Cached values are stored in the `.qtype-cache/` directory in your working directory.

### Monitoring Cache Performance

Use the `--progress` flag to see cache hits and misses:

```bash
qtype run app.qtype.yaml --flow my_flow --progress
```

First run shows cache misses:
```
Step classify    ✔ 5 succeeded ✖ 0 errors ⟳ 0 hits ✗ 5 misses
```

Subsequent runs show cache hits (much faster):
```
Step classify    ✔ 5 succeeded ✖ 0 errors ⟳ 5 hits ✗ 0 misses
```

## Complete Example

```yaml
--8<-- "../examples/data_processing/cache_step_results.qtype.yaml"
```

Run the example:
```bash
# First run - cold cache
qtype run examples/data_processing/cache_step_results.qtype.yaml --progress -i '{"file_path": "examples/data_processing/sample_documents.jsonl"}'

# Second run - warm cache (much faster)
qtype run examples/data_processing/cache_step_results.qtype.yaml  --progress -i '{"file_path": "examples/data_processing/sample_documents.jsonl"}'

```

## See Also

- [LLMInference Reference](../../components/LLMInference.md)
- [Adjust Concurrency](adjust_concurrency.md)
- [Tutorial: Your First QType Application](../../Tutorials/your_first_qtype_application.md)
