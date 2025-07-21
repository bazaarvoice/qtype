from openinference.instrumentation.llama_index import LlamaIndexInstrumentor
from phoenix.otel import register as register_phoenix

from qtype.semantic.model import TelemetrySink


def register(telemetry: TelemetrySink, project_id: str | None = None) -> None:
    """Register a telemetry instance."""

    # Only llama_index and phoenix are supported for now
    # TODO: Add support for langfues and llamatrace
    tracer_provider = register_phoenix(
        endpoint=telemetry.endpoint,
        project_name=project_id if project_id else telemetry.id,
    )
    LlamaIndexInstrumentor().instrument(tracer_provider=tracer_provider)
