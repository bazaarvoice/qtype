from functools import partial
from typing import Any, Tuple

import pandas as pd

from qtype.interpreter.batch.types import BatchConfig
from qtype.interpreter.batch.utils import (
    batch_iterator,
    single_step_adapter,
    validate_inputs,
)
from qtype.interpreter.exceptions import InterpreterError
from qtype.semantic.model import (
    Condition,
    Decoder,
    PromptTemplate,
    Search,
    Step,
    Tool,
)

SINGLE_WRAP_STEPS = {Decoder, Condition, PromptTemplate, Search, Tool}


def batch_execute_step(
    step: Step,
    inputs: pd.DataFrame,
    batch_config: BatchConfig,
    **kwargs: dict[str, Any],
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Executes a given step in a batch processing pipeline.

    Args:
        step (Step): The step to be executed.
        inputs (pd.DataFrame): The input data for the step.
        batch_config (BatchConfig): Configuration for batch processing.
        **kwargs: Additional keyword arguments.

    Returns:
        Tuple[pd.DataFrame, pd.DataFrame]: A tuple containing the output results and any rows that returned errors.
    """

    validate_inputs(inputs, step)

    if step in SINGLE_WRAP_STEPS:
        return batch_iterator(
            f=partial(single_step_adapter, step=step),
            batch=inputs,
            batch_config=batch_config,
        )
    # TODO: implement batching for multi-row steps. For example, llm inference can be sped up in batch...
    else:
        raise InterpreterError(f"Unsupported step type: {type(step).__name__}")
