from __future__ import annotations

import logging
from typing import Any, Tuple

import pandas as pd

from qtype.interpreter.batch.step import batch_execute_step
from qtype.interpreter.batch.types import BatchConfig
from qtype.interpreter.batch.utils import reconcile_results_and_errors
from qtype.semantic.model import Flow, Sink

logger = logging.getLogger(__name__)


def batch_execute_flow(
    flow: Flow,
    inputs: pd.DataFrame,
    batch_config: BatchConfig,
    **kwargs: dict[Any, Any],
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Executes a flow in a batch context.

    Args:
        flow: The flow to execute.
        batch_config: The batch configuration to use.
        **kwargs: Additional keyword arguments to pass to the flow.

    Returns:
        A list of output variables produced by the flow.
    """

    previous_outputs = inputs

    # Iterate over each step in the flow
    for step in flow.steps:
        results: list[pd.DataFrame] = []
        errors: list[pd.DataFrame] = []

        if isinstance(step, Sink):
            # Send the entire batch to the sink
            batch_results, batch_errors = batch_execute_step(
                step, previous_outputs, batch_config
            )
            results.append(batch_results)
            if len(batch_errors) > 1:
                errors.append(batch_errors)
        else:
            # batch the current data into dataframes of max size batch_size
            batch_size = batch_config.batch_size
            for start in range(0, len(previous_outputs), batch_size):
                end = start + batch_size
                batch = previous_outputs.iloc[start:end]
                # Execute the step with the current batch
                batch_results, batch_errors = batch_execute_step(
                    step, batch, batch_config
                )

                results.append(batch_results)
                if len(batch_errors) > 1:
                    errors.append(batch_errors)

        previous_outputs, errors_df = reconcile_results_and_errors(
            results, errors
        )

        if len(errors_df) and batch_config.write_errors_to:
            output_file = (
                f"{batch_config.write_errors_to}/{step.id}.errors.parquet"
            )
            try:
                errors_df.to_parquet(
                    output_file, engine="pyarrow", compression="snappy"
                )
                logging.info(
                    f"Saved errors for step {step.id} to {output_file}"
                )
            except Exception as e:
                logging.warning(
                    f"Could not save errors step {step.id} to {output_file}",
                    exc_info=e,
                    stack_info=True,
                )

    # Return the last steps results and errors
    return previous_outputs, errors_df
