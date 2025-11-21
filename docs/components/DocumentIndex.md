### DocumentIndex

Document search index for text-based search (e.g., Elasticsearch, OpenSearch).

- **type** (`Literal`): (No documentation available.)
- **endpoint** (`str`): URL endpoint for the search cluster (e.g., https://my-cluster.es.amazonaws.com).
- **id_field** (`str | None`): Field name to use as document ID. If not specified, auto-detects from: _id, id, doc_id, document_id, or uuid. If all are missing, a UUID is generated.
