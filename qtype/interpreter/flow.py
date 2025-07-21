from __future__ import annotations

import logging
from typing import Any

from qtype.interpreter.exceptions import InterpreterError
from qtype.interpreter.step import execute_step
from qtype.semantic.model import Flow, Variable

logger = logging.getLogger(__name__)


def execute_flow(flow: Flow, **kwargs: dict[Any, Any]) -> list[Variable]:
    """Execute a flow based on the provided arguments.

    Args:
        flow: The flow to execute.
        inputs: The input variables for the flow.
        **kwargs: Additional keyword arguments.
    """
    logger.debug(f"Executing step: {flow.id} with kwargs: {kwargs}")

    unset_inputs = [input for input in flow.inputs if not input.is_set()]
    if unset_inputs:
        raise InterpreterError(
            f"The following inputs are required but have no values: {', '.join([input.id for input in unset_inputs])}"
        )

    for step in flow.steps:
        execute_step(step, **kwargs)

    unset_outputs = [output for output in flow.outputs if not output.is_set()]
    if unset_outputs:
        raise InterpreterError(
            f"The following outputs are required but have no values: {', '.join([output.id for output in unset_outputs])}"
        )
    return flow.outputs
