# Telemetry

Telemetry provides comprehensive observability and monitoring capabilities for QType applications, enabling developers to track performance, debug issues, and gain insights into application behavior. It captures metrics, traces, and logs across all components including steps, flows, model interactions, and tool executions.

Telemetry is essential for production deployments, allowing teams to monitor application health, optimize performance, identify bottlenecks, and troubleshoot issues in real-time or through historical analysis.

Only one telemetry sink can be configured per application. For multiple destinations, use a telemetry aggregator like OpenTelemetry Collector.

## Component Definition

--8<-- "components/TelemetrySink.md"


## Related Concepts

Telemetry observes all QType components including [Steps](../Steps/index.md), [Flows](flow.md), [Models](model.md), [Tools](tool.md), and [Memory](memory.md). It integrates with [AuthorizationProvider](authorization-provider.md) for secure data export and provides insights for optimizing [Variable](variable.md) data flow.

## Example Usage

