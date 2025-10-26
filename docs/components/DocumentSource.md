### DocumentSource

A source of documents that will be used in retrieval augmented generation.
It uses LlamaIndex readers to load one or more raw Documents
from a specified path or system (e.g., Google Drive, web page).
See https://github.com/run-llama/llama_index/tree/main/llama-index-integrations/readers

- **type** (`Literal`): (No documentation available.)
- **reader_module** (`str`): Module path of the LlamaIndex Reader without 'llama_index.readers' (e.g., 'google.GoogleDriveReader', 'file.IPYNBReader').
- **args** (`dict[str, Any]`): Reader-specific arguments to pass to the LlamaIndex constructor.
- **auth** (`Reference[AuthProviderType] | str | None`): AuthorizationProvider for accessing the source.
