from __future__ import annotations

from openinference.instrumentation.llama_index import LlamaIndexInstrumentor
from phoenix.otel import register as register_phoenix

from qtype.interpreter.base.secrets import SecretManagerBase
from qtype.semantic.model import TelemetrySink


def register(
    telemetry: TelemetrySink,
    project_id: str | None = None,
    secret_manager: SecretManagerBase | None = None,
) -> None:
    """
    Register and configure telemetry for the QType runtime.

    This function sets up telemetry collection by:
    1. Resolving any SecretReferences in the telemetry endpoint
    2. Registering with the Phoenix OTEL provider
    3. Instrumenting LlamaIndex for automatic tracing

    Args:
        telemetry: TelemetrySink configuration with endpoint and auth
        project_id: Optional project identifier for telemetry grouping.
            If not provided, uses telemetry.id
        secret_manager: Optional secret manager for resolving endpoint URLs
            that are stored as SecretReferences. If None, uses NoOpSecretManager
            which will raise an error if secrets are needed.

    Note:
        Currently only supports LlamaIndex and Phoenix. Support for
        Langfuse and LlamaTrace is planned.
    """
    from qtype.interpreter.base.secrets import NoOpSecretManager

    # Only llama_index and phoenix are supported for now
    # TODO: Add support for langfues and llamatrace
    if secret_manager is None:
        secret_manager = NoOpSecretManager()

    context = f"telemetry sink '{telemetry.id}'"
    endpoint = secret_manager(telemetry.endpoint, context)
    tracer_provider = register_phoenix(
        endpoint=endpoint,
        project_name=project_id if project_id else telemetry.id,
    )
    LlamaIndexInstrumentor().instrument(tracer_provider=tracer_provider)
