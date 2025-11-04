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

    Attributes:
        secret_manager: Secret manager for resolving SecretReferences at
            runtime. None if no secret management is configured.
        on_stream_event: Optional callback for streaming real-time execution
            events (chunks, steps, errors) to clients.
        on_progress: Optional callback for progress updates during execution.
        tracer: OpenTelemetry tracer for distributed tracing and observability.
            Defaults to a no-op tracer if telemetry is not configured.

    Example:
        ```python
        from qtype.interpreter.base.executor_context import ExecutorContext
        from opentelemetry import trace

        context = ExecutorContext(
            secret_manager=my_secret_manager,
            on_stream_event=my_stream_callback,
            tracer=trace.get_tracer(__name__)
        )

        executor = create_executor(step, context=context)
        ```
    """

    secret_manager: SecretManagerBase | None = None
    on_stream_event: StreamingCallback | None = None
    on_progress: ProgressCallback | None = None
    tracer: Tracer | None = None
