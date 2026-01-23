# Read Data from Files

Load structured data from files using FileSource, which supports CSV, JSON, JSONL, and Parquet formats with automatic format detection and type conversion.

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
- **Type conversion**: Automatically converts data to match variable types (primitives, domain types, custom types)
- **Streaming**: Emits one FlowMessage per row, enabling downstream steps to process data in parallel

### Automatic Type Conversion

FileSource automatically converts data from files to match your variable types:

- **Primitive types** (`int`, `float`, `bool`, `text`): Direct conversion from file data
- **Domain types** (`ChatMessage`, `SearchResult`, etc.): Validated from dict/object columns
- **Custom types**: Your defined types are validated and instantiated from dict/object columns

**Format Recommendations:**

- **CSV**: Best for simple primitive types (strings, numbers, booleans)
- **JSON/JSONL**: Recommended for nested objects, custom types, and domain types
- **Parquet**: Best for large datasets with mixed types and efficient storage

**Example with Custom Types (JSON format):**

```json
[
  {"person": {"name": "Alice", "age": 30}, "score": 95},
  {"person": {"name": "Bob", "age": 25}, "score": 87}
]
```

JSON preserves nested objects, making it ideal for complex types. CSV stores everything as strings, requiring nested objects to be serialized as JSON strings within the CSV.

## Complete Example

```yaml
--8<-- "../examples/data_processing/read_file.qtype.yaml"
```

## See Also

- [FileSource Reference](../../components/FileSource.md)
- [Example: Batch Processing](../../Gallery/Data%20Processing/batch_processing.md)
