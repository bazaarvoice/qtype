### SQLSource

SQL database source that executes queries and emits rows.

- **type** (`Literal`): (No documentation available.)
- **query** (`str`): SQL query to execute. Inputs are injected as params.
- **connection** (`str | SecretReference`): Database connection string or reference to auth provider. Typically in SQLAlchemy format.
- **auth** (`Reference[AuthProviderType] | str | None`): Optional AuthorizationProvider for database authentication.
