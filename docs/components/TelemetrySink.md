### TelemetrySink

Defines an observability endpoint for collecting telemetry data from the QType runtime.

- **id** (`str`): Unique ID of the telemetry sink configuration.
- **provider** (`Literal`): (No documentation available.)
- **auth** (`Reference[AuthProviderType] | str | None`): AuthorizationProvider used to authenticate telemetry data transmission.
- **endpoint** (`str | SecretReference`): URL endpoint where telemetry data will be sent.
- **args** (`dict[str, Any]`): Additional configuration arguments specific to the telemetry sink type.
