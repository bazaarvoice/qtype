# Read Data from Files

Load structured data from files using FileSource, which supports CSV, JSON, JSONL, and Parquet formats with automatic format detection based on file extension.

### QType YAML

```yaml
steps:
  - id: read_data
    type: FileSource
    path: batch_inputs.csv
    outputs:
      - query
      - topic
```

### Explanation

- **FileSource**: Step that reads structured data from files using fsspec-compatible URIs
- **path**: File path (relative to YAML file or absolute), supports local files and cloud storage (s3://, gs://, etc.)
- **outputs**: Column names from the file to extract as variables (must match actual column names)
- **Format detection**: Automatically determined by file extension (.csv, .json, .jsonl, .parquet)
- **Streaming**: Emits one FlowMessage per row, enabling downstream steps to process data in parallel

## Complete Example

```yaml
--8<-- "../examples/data_processing/read_file.qtype.yaml"
```

## See Also

- [FileSource Reference](../../components/FileSource.md)
- [Aggregate Reference](../../components/Aggregate.md)
- [Example: Batch Processing](../../Gallery/Data%20Processing/batch_processing.md)
