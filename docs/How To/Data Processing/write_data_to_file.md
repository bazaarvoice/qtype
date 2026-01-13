# Write Data to a File

Write flow data to files using the `FileWriter` step, which accumulates all messages and outputs data in Parquet format using fsspec-compatible URIs.

### QType YAML

```yaml
steps:
  - type: FileWriter
    id: write_results
    path: output_path          # Variable containing file path
    inputs:
      - review_id
      - product_name
      - rating
      - llm_analysis
      - output_path
    outputs:
      - result_file
```

### Explanation

- **FileWriter**: Batches all incoming messages and writes them as a single Parquet file
- **path**: fsspec-compatible URI (can be a `ConstantPath`, Variable reference, or string) for the output file location
- **inputs**: Variables from FlowMessages to include as columns in the output file
- **outputs**: Variable containing the path where data was written (useful for passing to downstream steps)
- **batch_config**: Optional configuration for batch size. This defaults to max_int (i.e., processes all messages into one file). If you change it, you will get multiple files.

## Complete Example
See the [LLM Processing Pipelines](../../Gallery/dataflow_pipelines.md) gallery example.



## See Also

- [FileWriter Reference](../../components/FileWriter.md)
- [Read Data from Files](read_data_from_files.md)
- [Read SQL Databases](read_sql_databases.md)
- [LLM Processing Pipelines](../../Gallery/dataflow_pipelines.md)
