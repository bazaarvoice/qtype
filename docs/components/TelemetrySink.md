# TelemetrySink

Defines an observability endpoint for collecting telemetry data from the QType runtime.

## Members
- **id** (`str`): Unique ID of the telemetry sink configuration.
- **auth** (`AuthorizationProvider | str | None`): AuthorizationProvider used to authenticate telemetry data transmission.
- **endpoint** (`str`): URL endpoint where telemetry data will be sent.

---
