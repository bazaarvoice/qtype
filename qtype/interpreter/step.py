from __future__ import annotations

import logging
from typing import Any

from qtype.interpreter.exceptions import InterpreterError
from qtype.interpreter.steps import (
    agent,
    condition,
    decoder,
    llm_inference,
    prompt_template,
    search,
    tool,
)
from qtype.semantic.model import (
    Agent,
    Condition,
    Decoder,
    Flow,
    LLMInference,
    PromptTemplate,
    Search,
    Step,
    Tool,
    Variable,
)

logger = logging.getLogger(__name__)


def execute_step(step: Step, **kwargs: dict[str, Any]) -> list[Variable]:
    """Execute a single step within a flow.

    Args:
        step: The step to execute.
        **kwargs: Additional keyword arguments.
    """
    logger.debug(f"Executing step: {step.id} with kwargs: {kwargs}")

    unset_inputs = [input for input in step.inputs if not input.is_set()]
    if unset_inputs:
        raise InterpreterError(
            f"The following inputs are required but have no values: {', '.join([input.id for input in unset_inputs])}"
        )

    if isinstance(step, Agent):
        return agent.execute(step=step, **kwargs)  # type: ignore[arg-type]
    elif isinstance(step, Condition):
        return condition.execute(condition=step, **kwargs)
    elif isinstance(step, Decoder):
        return decoder.execute(step=step, **kwargs)  # type: ignore[arg-type]
    elif isinstance(step, Flow):
        from .flow import execute_flow

        return execute_flow(step, **kwargs)  # type: ignore[arg-type]
    elif isinstance(step, LLMInference):
        return llm_inference.execute(step, **kwargs)  # type: ignore[arg-type]
    elif isinstance(step, PromptTemplate):
        return prompt_template.execute(step, **kwargs)  # type: ignore[arg-type]
    elif isinstance(step, Search):
        return search.execute(step, **kwargs)  # type: ignore[arg-type]
    elif isinstance(step, Tool):
        return tool.execute(step, **kwargs)  # type: ignore[arg-type]
    else:
        # Handle other step types if necessary
        raise InterpreterError(f"Unsupported step type: {type(step).__name__}")
