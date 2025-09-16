from typing import Any, Tuple

import pandas as pd

from qtype.base.exceptions import InterpreterError
from qtype.interpreter.batch.types import BatchConfig, ErrorMode
from qtype.interpreter.batch.utils import (
    reconcile_results_and_errors,
    validate_inputs,
)
from qtype.semantic.model import FileSink, FileSource


def _get_file_path(step: FileSource | FileSink, row: pd.Series) -> str:
    """Get the file path from either the step's path field or input variable.

    Args:
        step: The FileSource or FileSink step.
        row: The current input row being processed.

    Returns:
        The file path to use.

    Raises:
        InterpreterError: If path cannot be determined.
    """
    if step.path is not None:
        return step.path

    # Look for 'path' in the input row
    if "path" in row.index:
        return str(row["path"])

    raise InterpreterError(
        f"No path specified for {type(step).__name__}. "
        "Either set the 'path' field or provide a 'path' input variable."
    )


def execute_file_source(
    step: FileSource,
    inputs: pd.DataFrame,
    batch_config: BatchConfig,
    **kwargs: dict[Any, Any],
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Executes a FileSource step to read data from a file using fsspec.

    Args:
        step: The FileSource step to execute.
        inputs: Input DataFrame (may contain path variable).
        batch_config: Configuration for batch processing.
        **kwargs: Additional keyword arguments.

    Returns:
        A tuple containing two DataFrames:
            - The first DataFrame contains the successfully read data.
            - The second DataFrame contains rows that encountered errors with an 'error' column.
    """
    validate_inputs(inputs, step)

    output_columns = {output.id for output in step.outputs}

    results = []
    errors = []

    # FileSource has cardinality 'many', so it reads once and produces multiple output rows
    # We process each input row (which might have different paths) separately
    for _, row in inputs.iterrows():
        try:
            file_path = _get_file_path(step, row)

            # Use fsspec to read the file
            df = pd.read_parquet(file_path)

            # Filter to only the expected output columns if they exist
            if output_columns and len(df) > 0:
                available_columns = set(df.columns)
                missing_columns = output_columns - available_columns
                if missing_columns:
                    raise InterpreterError(
                        f"File {file_path} missing expected columns: {', '.join(missing_columns)}. "
                        f"Available columns: {', '.join(available_columns)}"
                    )
                df = df[[col for col in df.columns if col in output_columns]]

            results.append(df)

        except Exception as e:
            if batch_config.error_mode == ErrorMode.FAIL:
                raise e

            # If there's an error, add it to the errors list
            error_df = pd.DataFrame([{"error": str(e)}])
            errors.append(error_df)

    return reconcile_results_and_errors(results, errors)


def execute_file_sink(
    step: FileSink,
    inputs: pd.DataFrame,
    batch_config: BatchConfig,
    **kwargs: dict[Any, Any],
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Executes a FileSink step to write data to a file using fsspec.

    Args:
        step: The FileSink step to execute.
        inputs: Input DataFrame containing data to write.
        batch_config: Configuration for batch processing.
        **kwargs: Additional keyword arguments.

    Returns:
        A tuple containing two DataFrames:
            - The first DataFrame contains success indicators.
            - The second DataFrame contains rows that encountered errors with an 'error' column.
    """
    validate_inputs(inputs, step)

    # Get file paths for all rows
    file_paths = []
    for _, row in inputs.iterrows():
        try:
            file_path = _get_file_path(step, row)
            file_paths.append(file_path)
        except Exception as e:
            if batch_config.error_mode == ErrorMode.FAIL:
                raise e
            # If we can't get the path, we can't proceed
            error_df = pd.DataFrame([{"error": str(e)}])
            return pd.DataFrame(), error_df

    # Check if all paths are the same
    unique_paths = list(set(file_paths))

    if len(unique_paths) == 1:
        # All rows write to the same file - process as one batch
        file_path = unique_paths[0]

        try:
            # Use pandas to write directly to the fsspec path
            inputs.to_parquet(file_path, index=False)

            # Create success result for all rows
            success_df = pd.DataFrame(
                [{"success": True, "file_path": file_path}]
            )
            return success_df, pd.DataFrame()

        except Exception as e:
            if batch_config.error_mode == ErrorMode.FAIL:
                raise e

            # If there's an error, return error for all rows
            error_df = pd.DataFrame([{"error": str(e)}])
            return pd.DataFrame(), error_df

    else:
        # Multiple unique paths - split inputs and process recursively
        all_results = []
        all_errors = []

        for unique_path in unique_paths:
            # Create mask for rows with this path
            path_mask = [
                _get_file_path(step, row) == unique_path
                for _, row in inputs.iterrows()
            ]
            sliced_inputs = inputs[path_mask]

            # Recursively call execute_file_sink with the sliced DataFrame
            results, errors = execute_file_sink(
                step, sliced_inputs, batch_config, **kwargs
            )

            if len(results) > 0:
                all_results.append(results)
            if len(errors) > 0:
                all_errors.append(errors)

        return reconcile_results_and_errors(all_results, all_errors)
