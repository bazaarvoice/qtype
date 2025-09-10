from __future__ import annotations

import copy
from typing import Any, Callable, Tuple

import pandas as pd

from qtype.interpreter.batch.types import BatchConfig, ErrorMode
from qtype.semantic.model import Step


class InputMissingError(Exception):
    """Raised when a required input variable is missing from the DataFrame."""

    pass


def validate_inputs(batch: pd.DataFrame, step: Step) -> pd.DataFrame:
    """Ensures all input variables for the step are columns in the DataFrame.
    If not, an Exception is raised.

    Args:
        batch: The input DataFrame to decode.
        decoder: The decoder step to validate.

    Returns:
        A view of the dataframe with only the input columns for the step.

    Raises:
        InputMissingError: If the decoder step does not have exactly one input or if the input column is not in the DataFrame.
    """
    input_ids = [input_var.id for input_var in step.inputs]
    for input_var in input_ids:
        if input_var not in batch.columns:
            raise InputMissingError(
                f"Input DataFrame must contain column '{input_var}' for step {step.id}."
            )
    return batch[input_ids]


def fail_mode_wrapper(
    f: Callable[..., dict[str, Any]],
    row: pd.Series,
    batch_config: BatchConfig,
    **kwargs: dict[str, Any],
) -> dict | Exception:
    """Executes a function with error handling based on the batch configuration.

    Args:
        f: The function to execute that can take any arguments and returns a dict of results.
        row: The input row as a dictionary.
        batch_config: Configuration for error handling.
        **kwargs: Additional keyword arguments.

    Returns:
        The result of the function or an Exception if an error occurs and the error mode is set to CONTINUE.
    """
    try:
        # turn row into a dict and merge with kwargs
        merged_kwargs = {**row.to_dict(), **kwargs}
        return f(**merged_kwargs)
    except Exception as e:
        if batch_config.error_mode == ErrorMode.FAIL:
            raise e
        else:
            return e


def single_step_adapter(
    step: Step, **inputs: dict[str, Any]
) -> dict[str, Any]:
    """A batch adapter for steps that have no side effects or access shared resources."""
    from qtype.interpreter.step import execute_step

    step_clone = copy.deepcopy(step)
    for input_var in step_clone.inputs:
        if input_var.id in inputs:
            input_var.value = inputs[input_var.id]
        else:
            raise ValueError(
                f"Input variable '{input_var.id}' not found in inputs."
            )
    execute_step(step_clone)
    return {
        output_var.id: output_var.value for output_var in step_clone.outputs
    }


def to_series(
    rv: dict | Exception, error_col_name: str = "error"
) -> pd.Series:
    # If rv is an exception, return a series with index "error"
    if isinstance(rv, Exception):
        return pd.Series({error_col_name: str(rv)})
    return pd.Series(rv)  # type: ignore[no-any-return]


def batch_iterator(
    f: Callable[..., dict[str, Any]],
    batch: pd.DataFrame,
    batch_config: BatchConfig,
    **kwargs: Any,
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Executes a step over a batch of inputs with error handling.

    Args:
        step: The step to execute.
        batch: The input DataFrame to process.
        batch_config: Configuration for error handling.
        **kwargs: Additional keyword arguments to pass to the step.

    Returns:
        A tuple containing two DataFrames:
            - The first DataFrame contains successful results with output columns.
            - The second DataFrame contains rows that encountered errors with an 'error' column.
    """

    # Use a unique column name for errors
    error_col = "error_" + str(id(f))

    # If error_col is already in the dataframe, throw an exception
    if error_col in batch.columns:
        raise ValueError(
            f"Error column name '{error_col}' already exists in the batch DataFrame."
        )

    def the_pipe(row: pd.Series) -> pd.Series:
        return to_series(
            fail_mode_wrapper(f, row, batch_config=batch_config, **kwargs),
            error_col_name=error_col,
        )

    results = batch.apply(the_pipe, axis=1)

    # Split the results into two dataframes, one where error_col is not defined, and one where it is.
    success_mask = ~results[error_col].notna()
    failed_mask = results[error_col].notna()

    # Create success DataFrame (drop the error column)
    success_df = results[success_mask].drop(columns=[error_col])

    # Create failed DataFrame (keep only original columns plus error)
    original_columns = batch.columns.tolist()

    if failed_mask.any():
        failed_df = results[failed_mask]
        # Drop all the output columns from failed_df, keep only original input columns + error
        failed_df = failed_df[original_columns + [error_col]]
    else:
        # No failed rows, create empty DataFrame with expected structure
        failed_df = pd.DataFrame(columns=original_columns + [error_col])

    return success_df, failed_df


def reconcile_results_and_errors(
    results: list[pd.DataFrame], errors: list[pd.DataFrame]
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Concatenates lists of pandas DataFrames containing results and errors into single DataFrames.

    If the input lists are empty, creates empty DataFrames as placeholders.

    Args:
        results (list[pd.DataFrame]): List of DataFrames containing results.
        errors (list[pd.DataFrame]): List of DataFrames containing errors.

    Returns:
        Tuple[pd.DataFrame, pd.DataFrame]: A tuple containing:
            - A single DataFrame with all results concatenated.
            - A single DataFrame with all errors concatenated.
    """
    if not results:
        results = [pd.DataFrame({})]
    if not errors:
        errors = [pd.DataFrame({})]
    return pd.concat(results, ignore_index=True), pd.concat(
        errors, ignore_index=True
    )
