# Serve Flows as APIs

Expose your QType flows as HTTP REST endpoints with automatically generated OpenAPI documentation using the `qtype serve` command.

### Command

```bash
qtype serve <file.qtype.yaml> [--host HOST] [--port PORT] [--reload]
```

### Explanation

- **Swagger UI**: Interactive API documentation available at `http://localhost:8000/docs`
- **ReDoc**: Alternative API documentation at `http://localhost:8000/redoc`
- **REST Endpoints**: Each flow is available at `POST /invoke/{flow_id}`
- **Streaming Endpoints**: Flows with UI interfaces get `POST /stream/{flow_id}` for Server-Sent Events
- **Interactive UI**: Web interface at `http://localhost:8000/ui` (redirects from root)
- **--reload**: Auto-reload on file changes during development
- **--host/--port**: Override default host (localhost) and port (8000)

### Example

```bash
qtype serve examples/tutorials/01_hello_world.qtype.yaml
```

Then visit `http://localhost:8000/docs` to explore and test your API endpoints.

### Available Endpoints

- **`GET /flows`**: List all flows with metadata (inputs, outputs, interface type)
- **`POST /flows/{flow_id}`**: Execute a specific flow (e.g., `POST /flows/simple_example`)

Each flow endpoint accepts JSON input matching the flow's input schema and returns structured results with `outputs` and `errors` arrays.

## See Also

- [Application Reference](../../components/Application.md)
- [Flow Reference](../../components/Flow.md)
- [FlowInterface Reference](../../components/FlowInterface.md)
