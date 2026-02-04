# Load Documents

Load documents from files, directories, or external systems using LlamaIndex readers with DocumentSource.

**Note:** DocumentSource is a source step that generates data independently, so flows using it typically require no inputs.

### QType YAML

```yaml
steps:
  - type: DocumentSource
    id: load_docs
    reader_module: llama_index.core.SimpleDirectoryReader
    args:
      input_dir: ./data
      required_exts: [".md", ".txt"]
      recursive: true
    loader_args:
      num_workers: 4
    outputs:
      - document
```

### Explanation

- **reader_module**: Python module path to a class that inherits from `llama_index.core.readers.base.BaseReader` (most common: `llama_index.core.SimpleDirectoryReader`)
- **args**: Arguments passed to the reader class constructor (e.g., `input_dir`, `required_exts`, `recursive`, `file_extractor`)
- **loader_args**: Arguments passed to the reader's `load_data()` method (e.g., `num_workers` for parallel processing)
- **outputs**: Variable to store loaded documents (type: `RAGDocument`) - DocumentSource fans out, emitting one message per document
- **Critical distinction**: Constructor args configure the reader instance; `load_data` args control how documents are loaded

### Common Reader Modules

**SimpleDirectoryReader** (`llama_index.core.SimpleDirectoryReader`):
- Constructor args: `input_dir`, `input_files`, `required_exts`, `exclude`, `recursive`, `file_extractor`, `file_metadata`, `encoding`
- Loader args: `num_workers` (parallel processing)
- Supports 15+ file types including PDF, DOCX, CSV, Markdown, images, audio/video
- [Full documentation](https://developers.llamaindex.ai/python/framework/module_guides/loading/simpledirectoryreader/)

**JSONReader** (`llama_index.readers.json.JSONReader`):
- Constructor args: `levels_back`, `collapse_length`, `ensure_ascii`, `is_jsonl`, `clean_json`
- Loader args: `input_file`, `extra_info`
- Supports both JSON and JSONL (JSON Lines) formats
- [Full documentation](https://developers.llamaindex.ai/typescript/framework/modules/data/readers/json/)

### Dynamic Arguments

You can pass flow variables as constructor arguments by including them in `args`. At runtime, QType merges message variables with the configured args:

```yaml
variables:
  - id: data_path
    type: text

steps:
  - type: DocumentSource
    id: load_docs
    reader_module: llama_index.core.SimpleDirectoryReader
    args:
      input_dir: data_path    # References variable from message
    inputs: [data_path]
```

## Complete Example

```yaml
--8<-- "../examples/data_processing/load_documents.qtype.yaml"
```

## See Also

- [DocumentSource Reference](../../components/DocumentSource.md)
- [DocumentSplitter How-To](chunk_documents.md)
- [RAG Tutorial](../../Tutorials/rag_tutorial.md)
