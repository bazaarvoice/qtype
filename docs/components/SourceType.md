### SQLSource

SQL database source that executes queries and emits rows.

- **query** (`str`): SQL query to execute. Inputs are injected as params.
- **connection** (`str`): Database connection string or reference to auth provider. Typically in SQLAlchemy format.
- **auth** (`AuthProviderType | str | None`): Optional AuthorizationProvider for database authentication.
