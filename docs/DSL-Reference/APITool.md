# APITool

Tool that invokes an API endpoint.

## Members
- **endpoint** (`str`): API endpoint URL to call.
- **method** (`str`): HTTP method to use (GET, POST, PUT, DELETE, etc.).
- **auth** (`AuthorizationProvider | str | None`): Optional AuthorizationProvider for API authentication.
- **headers** (`dict[str, str] | None`): Optional HTTP headers to include in the request.

---
