### Index

Base class for searchable indexes that can be queried by search steps.

- **id** (`str`): Unique ID of the index.
- **args** (`dict[str, Any]`): Index-specific configuration and connection parameters.
- **auth** (`Reference[AuthProviderType] | str | None`): AuthorizationProvider for accessing the index.
- **name** (`str`): Name of the index/collection/table.
