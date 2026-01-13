# Serve Flows as UI

Expose your QType flows through an interactive web interface using the `qtype serve` command.

### Command

```bash
qtype serve <file.qtype.yaml> [--host HOST] [--port PORT] [--reload]
```

### Explanation

- **Interactive UI**: Web interface at `http://localhost:8000/ui` (redirects from root `/`)
- **Complete Flows**: Display as forms with input fields and output display
- **Conversational Flows**: Display as chat interfaces with message history
- **Auto-generated**: UI is automatically created based on flow inputs/outputs
- **--reload**: Auto-reload on file changes during development
- **--host/--port**: Override default host (localhost) and port (8000)

### Example

```bash
qtype serve examples/tutorials/01_hello_world.qtype.yaml
```

Then visit `http://localhost:8000/ui` to interact with your flow through the web interface.

![Flow UI Screenshot](flow_as_ui.png)

The UI automatically generates:

- Input fields based on variable types
- Submit button to execute the flow
- Output display for results
- Error messages if execution fails

## See Also

- [Serve Flows as APIs](serve_flows_as_apis.md)
- [Flow Reference](../../components/Flow.md)
- [FlowInterface Reference](../../components/FlowInterface.md)
- [Tutorial: Build a Conversational Chatbot](../../Tutorials/02-conversational-chatbot.md)
