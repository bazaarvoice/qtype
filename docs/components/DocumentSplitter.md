### DocumentSplitter

Configuration for chunking/splitting documents into embeddable nodes/chunks.

- **type** (`Literal`): (No documentation available.)
- **cardinality** (`Literal`): Consumes one document and emits 0...N nodes/chunks.
- **splitter_name** (`str`): Name of the LlamaIndex TextSplitter class.
- **chunk_size** (`int`): Size of each chunk.
- **chunk_overlap** (`int`): Overlap between consecutive chunks.
- **args** (`dict[str, Any]`): Additional arguments specific to the chosen splitter class.
