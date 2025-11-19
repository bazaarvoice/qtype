from __future__ import annotations

import logging

from openinference.semconv.trace import (
    OpenInferenceSpanKindValues,
    SpanAttributes,
)
from opentelemetry import context as otel_context
from opentelemetry import trace
from opentelemetry.trace import Status, StatusCode

from qtype.interpreter.base import factory
from qtype.interpreter.base.executor_context import ExecutorContext
from qtype.interpreter.rich_progress import RichProgressCallback
from qtype.interpreter.types import FlowMessage
from qtype.semantic.model import Flow

logger = logging.getLogger(__name__)


async def run_flow(
    flow: Flow,
    initial: list[FlowMessage] | FlowMessage,
    show_progress: bool = False,
    **kwargs,
) -> list[FlowMessage]:
    """
    Main entrypoint for executing a flow.

    Args:
        flow: The flow to execute
        initial: Initial FlowMessage(s) to start execution
        **kwargs: Dependencies including:
            - context: ExecutorContext with cross-cutting concerns (optional)
            - Other executor-specific dependencies

    Returns:
        List of final FlowMessages after execution
    """
    from qtype.interpreter.base.secrets import NoOpSecretManager

    # Extract or create ExecutorContext
    exec_context = kwargs.pop("context", None)
    progress_callback = RichProgressCallback() if show_progress else None
    if exec_context is None:
        exec_context = ExecutorContext(
            secret_manager=NoOpSecretManager(),
            tracer=trace.get_tracer(__name__),
            on_progress=progress_callback,
        )
    else:
        if exec_context.on_progress is None and show_progress:
            exec_context.on_progress = progress_callback

    # Use tracer from context
    tracer = exec_context.tracer or trace.get_tracer(__name__)

    # Start a span for the entire flow execution
    span = tracer.start_span(
        f"flow.{flow.id}",
        attributes={
            "flow.id": flow.id,
            "flow.step_count": len(flow.steps),
            SpanAttributes.OPENINFERENCE_SPAN_KIND: (
                OpenInferenceSpanKindValues.CHAIN.value
            ),
        },
    )

    # Make this span the active context so step spans will nest under it
    # Only attach if span is recording (i.e., real tracer is configured)
    ctx = trace.set_span_in_context(span)
    token = otel_context.attach(ctx) if span.is_recording() else None

    try:
        # 1. Get the execution plan is just the steps in order
        execution_plan = flow.steps

        # 2. Initialize the stream
        if not isinstance(initial, list):
            initial = [initial]

        span.set_attribute("flow.input_count", len(initial))

        # Record input variables for observability
        if initial:
            import json

            try:
                input_vars = {
                    k: v for msg in initial for k, v in msg.variables.items()
                }
                span.set_attribute(
                    SpanAttributes.INPUT_VALUE,
                    json.dumps(input_vars, default=str),
                )
                span.set_attribute(
                    SpanAttributes.INPUT_MIME_TYPE, "application/json"
                )
            except Exception:
                # If serialization fails, skip it
                pass

        async def initial_stream():
            for message in initial:
                yield message

        current_stream = initial_stream()

        # 3. Chain executors together in the main loop
        for step in execution_plan:
            executor = factory.create_executor(step, exec_context, **kwargs)
            output_stream = executor.execute(
                current_stream,
            )
            current_stream = output_stream

        # 4. Collect the final results from the last stream
        final_results = [state async for state in current_stream]

        # Close the progress bars if any
        if progress_callback is not None:
            progress_callback.close()
        # Record flow completion metrics
        span.set_attribute("flow.output_count", len(final_results))
        error_count = sum(1 for msg in final_results if msg.is_failed())
        span.set_attribute("flow.error_count", error_count)

        # Record output variables for observability
        if final_results:
            import json

            try:
                output_vars = {
                    k: v
                    for msg in final_results
                    if not msg.is_failed()
                    for k, v in msg.variables.items()
                }
                span.set_attribute(
                    SpanAttributes.OUTPUT_VALUE,
                    json.dumps(output_vars, default=str),
                )
                span.set_attribute(
                    SpanAttributes.OUTPUT_MIME_TYPE, "application/json"
                )
            except Exception:
                # If serialization fails, skip it
                pass

        if error_count > 0:
            span.set_status(
                Status(
                    StatusCode.ERROR,
                    f"{error_count} of {len(final_results)} messages failed",
                )
            )
        else:
            span.set_status(Status(StatusCode.OK))

        return final_results

    except Exception as e:
        # Record the exception and set error status
        span.record_exception(e)
        span.set_status(Status(StatusCode.ERROR, f"Flow failed: {e}"))
        raise
    finally:
        # Detach the context and end the span
        # Only detach if we successfully attached (span was recording)
        if token is not None:
            otel_context.detach(token)
        span.end()
