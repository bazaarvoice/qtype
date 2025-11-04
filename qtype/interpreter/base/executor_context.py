"""
Execution context for flow and step executors.

This module provides the ExecutorContext dataclass that bundles cross-cutting
concerns threaded through the execution pipeline.
"""

from __future__ import annotations

from dataclasses import dataclass

from opentelemetry.trace import Tracer

from qtype.interpreter.base.secrets import SecretManagerBase
from qtype.interpreter.types import ProgressCallback, StreamingCallback


@dataclass
class ExecutorContext:
    """
    Runtime context for flow execution shared across all executors.

    This bundles cross-cutting concerns that need to be threaded through
    the execution pipeline but aren't specific to individual step types.
    Using a context object reduces parameter threading boilerplate while
    keeping dependencies explicit and testable.

    Secret Resolution Lifecycle:
        Secrets are resolved EARLY in the execution pipeline, following a
        fail-fast principle:

        1. At executor construction time, any SecretReferences in step
           configuration are resolved
        2. At auth context creation time, SecretReferences in auth providers
           are resolved (via auth() context manager)
        3. Resolution failures raise SecretResolutionError immediately,
           preventing execution from starting with invalid configuration

        This ensures:
        - Errors are caught before expensive operations begin
        - All secrets are validated at initialization
        - No partial execution with missing secrets
        - Clear, actionable error messages at startup

    Attributes:
        secret_manager: Secret manager for resolving SecretReferences at
            runtime. Always present (uses NoOpSecretManager if no secrets
            are configured), eliminating the need for None checks.
        on_stream_event: Optional callback for streaming real-time execution
            events (chunks, steps, errors) to clients.
        on_progress: Optional callback for progress updates during execution.
        tracer: OpenTelemetry tracer for distributed tracing and observability.
            Defaults to a no-op tracer if telemetry is not configured.

    Example:
        ```python
        from qtype.interpreter.base.executor_context import ExecutorContext
        from qtype.interpreter.base.secrets import create_secret_manager
        from opentelemetry import trace

        context = ExecutorContext(
            secret_manager=create_secret_manager(config),
            on_stream_event=my_stream_callback,
            tracer=trace.get_tracer(__name__)
        )

        executor = create_executor(step, context=context)
        ```
    """

    secret_manager: SecretManagerBase
    on_stream_event: StreamingCallback | None = None
    on_progress: ProgressCallback | None = None
    tracer: Tracer | None = None
