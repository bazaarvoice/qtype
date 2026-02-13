# Trace Calls with OpenTelemetry

Enable distributed tracing for your QType applications using OpenTelemetry to monitor LLM calls, execution times, and data flow through Phoenix or other observability platforms.

### QType YAML

```yaml
telemetry:
  id: phoenix_trace
  provider: Phoenix
  endpoint: http://localhost:6006/v1/traces
```

### Explanation

- **telemetry**: Top-level application configuration for observability
- **id**: Unique identifier for the telemetry sink
- **provider**: Telemetry backend (`Phoenix`, `Arize`, or `Langfuse`)
- **endpoint**: URL where OpenTelemetry traces are sent

### Starting Phoenix

Before running your application, start the Phoenix server:

```bash
python3 -m phoenix.server.main serve
```

Phoenix will start on `http://localhost:6006` where you can view traces and spans in real-time.

## Complete Example

```yaml
--8<-- "../examples/observability_debugging/trace_with_phoenix.qtype.yaml"
```

Run the example:

```bash
qtype run examples/observability_debugging/trace_with_phoenix.qtype.yaml --text "I love this product!"
```

Then open `http://localhost:6006` in your browser to see the traced execution.

## Complete Example for Arize Cloud

```yaml
--8<-- "../examples/observability_debugging/trace_with_arize.qtype.yaml"
```

## See Also

- [Application Reference](../../components/Application.md)
- [Validate QType YAML](validate_qtype_yaml.md)
- [CLI Reference](../../Reference/cli.md)
