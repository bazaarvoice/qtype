### DocumentSearch

Performs document search against a document index.

- **type** (`Literal`): (No documentation available.)
- **index** (`Reference[DocumentIndex] | str`): Index to search against (object or ID reference).
- **query_args** (`dict[str, Any]`): The arguments (other than 'query') to specify to the query shape (see https://docs.opensearch.org/latest/query-dsl/full-text/multi-match/).
