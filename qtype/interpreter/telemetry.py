from __future__ import annotations

import base64
import logging
from typing import cast

from openinference.instrumentation.llama_index import LlamaIndexInstrumentor
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.http.trace_exporter import (
    OTLPSpanExporter,
)
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

from qtype.interpreter.auth.generic import auth
from qtype.interpreter.base.secrets import SecretManagerBase
from qtype.semantic.model import APIKeyAuthProvider, TelemetrySink

logger = logging.getLogger(__name__)


def _setup_langfuse_otel(
    sink: TelemetrySink,
    project_id: str,
    secret_manager: SecretManagerBase,
    context: str,
) -> TracerProvider:
    """
    Initializes and registers Langfuse as an OTEL trace exporter.

    Langfuse supports OpenTelemetry via its OTLP-compatible endpoint at
    /api/public/otel. This function configures an OTLP exporter with
    Basic Auth credentials to send traces to Langfuse.

    Args:
        sink: TelemetrySink with Langfuse endpoint and credentials
        project_id: Project identifier for grouping traces in Langfuse
        secret_manager: For resolving secret references
        context: Context string for error messages

    Returns:
        Configured OpenTelemetry TracerProvider
    """
    # 1. Resolve secrets for Langfuse from args
    # Langfuse requires public_key and secret_key in args
    args = sink.args | {"host": sink.endpoint}
    args = secret_manager.resolve_secrets_in_dict(
        args, f"telemetry sink '{sink.id}' args"
    )

    public_key = args.get("public_key")
    secret_key = args.get("secret_key")

    if not public_key or not secret_key:
        msg = (
            f"Langfuse telemetry sink '{sink.id}' requires "
            "'public_key' and 'secret_key' in args. "
            f"Got keys: {list(args.keys())}"
        )
        raise ValueError(msg)

    # 2. Resolve the endpoint (host)
    host = args["host"]

    # 3. Build OTLP endpoint for Langfuse
    # Langfuse OTLP ingestion endpoint
    endpoint = f"{host.rstrip('/')}/api/public/otel"

    # 4. Create Basic Auth header
    # Langfuse uses Basic Auth with public_key:secret_key
    auth_string = f"{public_key}:{secret_key}"
    b64_auth = base64.b64encode(auth_string.encode()).decode()
    headers = {"Authorization": f"Basic {b64_auth}"}

    # 5. Setup OTEL Provider and Exporter
    # Set service.name resource, which maps to project_id in Langfuse
    resource = Resource(attributes={"service.name": project_id})
    tracer_provider = TracerProvider(resource=resource)

    # Create the OTLP exporter configured for Langfuse
    exporter = OTLPSpanExporter(endpoint=endpoint, headers=headers)
    tracer_provider.add_span_processor(BatchSpanProcessor(exporter))

    # Set as the global tracer provider
    trace.set_tracer_provider(tracer_provider)

    return tracer_provider


def _resolve_arize_credentials(
    sink: TelemetrySink,
    project_id: str,
    secret_manager: SecretManagerBase,
) -> tuple[str, str, str]:
    """Resolve Arize credentials from telemetry sink configuration.

    Args:
        sink: TelemetrySink with Arize configuration.
        project_id: Default project identifier if not in args.
        secret_manager: For resolving secret references.

    Returns:
        Tuple of (space_id, project_name, api_key).

    Raises:
        ValueError: If required credentials are missing or invalid.
    """
    if not sink.auth:
        raise ValueError(
            f"Arize telemetry sink '{sink.id}' requires "
            "'auth' field with an APIKeyAuthProvider."
        )
    space_id = sink.args.get("space_id", None)
    if not space_id:
        raise ValueError(
            f"Arize telemetry sink '{sink.id}' requires 'space_id' in args."
        )

    # Cast types since resolve_secrets_in_dict returns str (not SecretReference)
    space_id = cast(str, space_id)
    # Args project_name takes precedence over project_id parameter
    project_name = sink.args.get("project_name", project_id)

    # Resolve API key from auth provider
    with auth(sink.auth, secret_manager) as provider:
        if not isinstance(provider, APIKeyAuthProvider):
            raise ValueError(
                f"Arize telemetry sink '{sink.id}' requires "
                f"APIKeyAuthProvider, got {type(provider).__name__}"
            )
        # Cast since auth() context manager resolves SecretReferences to str
        api_key = cast(str, provider.api_key)

    return space_id, project_name, api_key


def _setup_arize_otel(
    sink: TelemetrySink,
    project_id: str,
    secret_manager: SecretManagerBase,
) -> TracerProvider:
    """Initialize and register Arize Cloud as an OTEL trace exporter.

    Uses the ``arize.otel.register()`` helper with HTTP transport.

    Args:
        sink: TelemetrySink with Arize endpoint and credentials.
        project_id: Project identifier for grouping traces.
        secret_manager: For resolving secret references in args.

    Returns:
        Configured OpenTelemetry TracerProvider.

    Raises:
        ValueError: If required credentials are missing or invalid.
    """
    # Resolve credentials
    space_id, project_name, api_key = _resolve_arize_credentials(
        sink, project_id, secret_manager
    )

    # Resolve endpoint
    config = {"endpoint": sink.endpoint}
    resolved = secret_manager.resolve_secrets_in_dict(
        config, f"telemetry sink '{sink.id}'"
    )
    endpoint = resolved.get("endpoint", "")
    if not endpoint:
        msg = f"Arize telemetry sink '{sink.id}' requires an 'endpoint' field."
        raise ValueError(msg)

    # Use HTTP transport (avoids gRPC TLS certificate issues)
    # Import arize here to allow GRPC env var to be set before pyarrow loads
    from arize.otel import register as arize_register
    from arize.otel.otel import Transport

    if "transport" in sink.args:
        # convert the string to Transport enum if provided
        transport_str = sink.args["transport"].upper()
        transport = Transport[transport_str]
    else:
        transport = Transport.GRPC

    tracer_provider = arize_register(
        space_id=space_id,
        api_key=api_key,
        project_name=project_name,
        endpoint=endpoint,
        transport=transport
    )

    return tracer_provider


def register(
    telemetry: TelemetrySink,
    secret_manager: SecretManagerBase,
    project_id: str | None = None,
) -> TracerProvider:
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

    Returns:
        TracerProvider instance for managing telemetry lifecycle.

    Note:
        Supports Phoenix, Langfuse, and Arize telemetry providers.
        Phoenix is the default.
    """
    project_id = project_id if project_id else telemetry.id

    if telemetry.provider == "Phoenix":
        from phoenix.otel import register as register_phoenix

        args = {
            "endpoint": telemetry.endpoint,
            "project_name": project_id,
        } | telemetry.args

        args = secret_manager.resolve_secrets_in_dict(
            args, f"telemetry sink '{telemetry.id}'"
        )
        tracer_provider = register_phoenix(**args)
    elif telemetry.provider == "Langfuse":
        tracer_provider = _setup_langfuse_otel(
            sink=telemetry,
            project_id=project_id,
            secret_manager=secret_manager,
            context=f"telemetry sink '{telemetry.id}'",
        )
    elif telemetry.provider == "Arize":
        tracer_provider = _setup_arize_otel(
            sink=telemetry,
            project_id=project_id,
            secret_manager=secret_manager,
        )
    else:
        raise ValueError(
            f"Unsupported telemetry provider: {telemetry.provider}"
        )
    LlamaIndexInstrumentor().instrument(tracer_provider=tracer_provider)
    return tracer_provider
