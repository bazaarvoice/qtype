from __future__ import annotations

import logging

from qtype.interpreter.base import factory
from qtype.interpreter.types import FlowMessage
from qtype.semantic.model import Flow

logger = logging.getLogger(__name__)


async def run_flow(
    flow: Flow, initial: list[FlowMessage] | FlowMessage, **kwargs
) -> list[FlowMessage]:
    """
    Main entrypoint for executing a flow.

    Args:
        flow: The flow to execute
        initial: Initial FlowMessage(s) to start execution
        **dependencies: Additional dependencies including:
            - on_stream_event: Optional StreamingCallback for real-time events
            - on_progress: Optional ProgressCallback for progress tracking
            - Other executor-specific dependencies

    Returns:
        List of final FlowMessages after execution
    """

    # 1. Get the execution plan is just the steps in order
    execution_plan = flow.steps

    # 2. Initialize the stream
    if not isinstance(initial, list):
        initial = [initial]

    async def initial_stream():
        for message in initial:
            yield message

    current_stream = initial_stream()

    # 3. Chain executors together in the main loop
    for step in execution_plan:
        executor = factory.create_executor(step, **kwargs)
        output_stream = executor.execute(
            current_stream,
        )
        current_stream = output_stream

    # 4. Collect the final results from the last stream
    final_results = [state async for state in current_stream]
    return final_results
