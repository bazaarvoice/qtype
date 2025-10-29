### FileWriter

File writer that writes data to a file using fsspec-compatible URIs.

- **type** (`Literal`): (No documentation available.)
- **path** (`ConstantPath | Reference[Variable] | str`): Reference to a variable with an fsspec-compatible URI to read from, or the uri itself.
- **batch_config** (`BatchConfig`): Configuration for processing the input stream in batches. If omitted, the step processes items one by one.
