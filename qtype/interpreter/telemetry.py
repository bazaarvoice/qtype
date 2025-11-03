from __future__ import annotations

from typing import TYPE_CHECKING, Any

from openinference.instrumentation.llama_index import LlamaIndexInstrumentor
from phoenix.otel import register as register_phoenix

from qtype.dsl.model import SecretReference
from qtype.semantic.model import TelemetrySink

if TYPE_CHECKING:
    from qtype.interpreter.secret_manager import SecretManagerBase


def _resolve_secret(
    value: str | SecretReference, secret_manager: SecretManagerBase | None
) -> str:
    """Resolve a secret value if it's a SecretReference."""
    if isinstance(value, str):
        return value
    if secret_manager is None:
        raise RuntimeError(
            "Cannot resolve SecretReference without a secret manager configured."
        )
    return secret_manager(value)


def register(
    telemetry: TelemetrySink,
    project_id: str | None = None,
    secret_manager: Any = None,
) -> None:
    """Register a telemetry instance."""

    # Only llama_index and phoenix are supported for now
    # TODO: Add support for langfues and llamatrace
    endpoint = _resolve_secret(telemetry.endpoint, secret_manager)  # type: ignore[arg-type]
    tracer_provider = register_phoenix(
        endpoint=endpoint,
        project_name=project_id if project_id else telemetry.id,
    )
    LlamaIndexInstrumentor().instrument(tracer_provider=tracer_provider)
