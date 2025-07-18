from __future__ import annotations

from typing import Any

from qtype.semantic.model import Condition, Variable


def execute(condition: Condition, **kwargs: dict[str, Any]) -> list[Variable]:
    """Execute a condition step.

    Args:
        condition: The condition step to execute.

    Returns:
        A list of variables that are set based on the condition evaluation.
    """
    from qtype.interpreter.step import execute_step

    if not condition.inputs:
        raise ValueError(
            "Condition step requires at least one input variable."
        )

    if len(condition.inputs) != 1:
        raise ValueError(
            f"Condition step {condition.id} must have exactly one input, found {len(condition.inputs)}."
        )
    input_var = condition.inputs[0]
    if condition.equals.value == input_var.value:  # type: ignore
        # If the condition is met, return the outputs
        return execute_step(condition.then, **kwargs)
    elif condition.else_:
        return execute_step(condition.else_, **kwargs)
    else:
        # If no else branch is defined, return an empty list
        return []
