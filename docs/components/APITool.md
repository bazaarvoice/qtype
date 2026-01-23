### APITool

Tool that invokes an API endpoint.

- **type** (`Literal`): (No documentation available.)
- **endpoint** (`str`): API endpoint URL to call.
- **method** (`str`): HTTP method to use (GET, POST, PUT, DELETE, etc.).
- **auth** (`Reference[AuthProviderType] | str | None`): Optional AuthorizationProvider for API authentication.
- **headers** (`dict[str, str]`): Optional HTTP headers to include in the request.
- **parameters** (`list[Variable]`): Path and query parameters for the API call.
