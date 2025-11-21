### Search

Base class for search operations against indexes.

- **filters** (`dict[str, Any]`): Optional filters to apply during search.
- **index** (`Reference[IndexType] | str`): Index to search against (object or ID reference).
- **default_top_k** (`int | None`): Number of top results to retrieve if not provided in the inputs.
