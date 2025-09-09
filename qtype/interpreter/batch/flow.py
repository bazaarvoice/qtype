from __future__ import annotations

import logging
from typing import Any

import pandas as pd

from qtype.interpreter.batch.step import batch_execute_step
from qtype.interpreter.batch.types import BatchConfig
from qtype.interpreter.exceptions import InterpreterError
from qtype.semantic.model import Flow, Sink, Variable

logger = logging.getLogger(__name__)


def batch_execute_flow(
    flow: Flow, batch_config: BatchConfig, **kwargs: dict[Any, Any]
) -> list[Variable]:
    """Executes a flow in a batch context.

    Args:
        flow: The flow to execute.
        batch_config: The batch configuration to use.
        **kwargs: Additional keyword arguments to pass to the flow.

    Returns:
        A list of output variables produced by the flow.
    """

    # Since flows have cardinality 1 (for now), create a DataFrame with a single row
    previous_outputs = pd.DataFrame(
        {input.id: input.value for input in flow.inputs}
    )

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

        # Combine all batch results into a single DataFrame
        if results:
            previous_outputs = pd.concat(results, ignore_index=True)
        else:
            # This is a terminal node with no outputs
            previous_outputs = pd.DataFrame(
                columns=[o.id for o in step.outputs]
            )

        if errors:
            errors_df = pd.concat(errors, ignore_index=True)  # type: ignore
            # Save the errors to disk if necessary
            if batch_config.write_errors_to:
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

    # Confirm there was a terminal node
    # Since flows have cardinality 1 (for now), this should be true.
    if len(previous_outputs) > 1:
        raise ValueError(
            f"All flows must terminate in one output, got {len(previous_outputs)}."
        )

    # Set the output variables so that we match other executors.
    outputs = (
        previous_outputs.to_dict(orient="records")[0]
        if len(previous_outputs) == 1
        else {}
    )
    for output in flow.outputs:
        if output.id in outputs:
            output.value = outputs[output.id]

    unset_outputs = [output for output in flow.outputs if not output.is_set()]
    if unset_outputs:
        raise InterpreterError(
            f"The following outputs are required but have no values: {', '.join([output.id for output in unset_outputs])}"
        )
    return flow.outputs
