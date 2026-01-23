# Load Multiple Inputs from Files

Process multiple inputs in batch by loading data from CSV, JSON, Parquet, or Excel files using the `--input-file` CLI flag, enabling bulk processing without manual JSON construction.

### CLI Command

```bash
qtype run app.qtype.yaml --input-file inputs.csv
```

### Supported File Formats

- **CSV**: Columns map to input variable names (best for primitive types)
- **JSON**: Array of objects or records format (best for nested/complex types)
- **Parquet**: Efficient columnar format for large datasets
- **Excel**: `.xlsx` or `.xls` files

### How It Works

When you provide `--input-file`, QType:
1. Reads the file into a pandas DataFrame
2. Automatically converts data to match input variable types
3. Each row becomes one execution of the flow
4. Column names must match flow input variable IDs
5. Processes rows with configured concurrency
6. Returns results as a DataFrame (can be saved with `--output`)

### Type Conversion

QType automatically converts file data to match your flow's input types:

- **Primitive types** (`int`, `float`, `bool`, `text`): Converted from file values
- **Custom types**: Validated and instantiated from dict/object columns (use JSON format)
- **Domain types**: Built-in types like `ChatMessage` or `SearchResult` (use JSON format)

**Format Selection Guide:**

- Use **CSV** for simple data with primitive types (strings, numbers, booleans)
- Use **JSON** for complex data with custom types, nested objects, or domain types
- Use **Parquet** for large datasets with mixed types and efficient storage

## Complete Example

**batch_inputs.csv:**
```csv
--8<-- "../examples/data_processing/batch_inputs.csv"
```

**Application:**
```yaml
--8<-- "../examples/data_processing/batch_processing.qtype.yaml"
```

**Run the batch:**
```bash
# Process all rows from CSV
qtype run batch_processing.qtype.yaml --input-file batch_inputs.csv

# Save results to Parquet
qtype run batch_processing.qtype.yaml \
  --input-file batch_inputs.csv \
  --output results.parquet
```

### Explanation

- **--input-file (-I)**: Path to file containing input data (CSV, JSON, Parquet, Excel)
- **Column mapping**: CSV column names must match flow input variable IDs exactly
- **Batch processing**: Each row is processed as a separate flow execution
- **--output (-o)**: Optional path to save results as Parquet file
- **Parallel processing**: Steps that support concurrency will process multiple rows in parallel

## See Also

<!-- - [Adjust Concurrency](adjust_concurrency.md) -->
<!-- - [FileSource Reference](../../components/FileSource.md) -->
- [Example: Dataflow Pipeline](../../Gallery/Data%20Processing/dataflow_pipelines.md)
