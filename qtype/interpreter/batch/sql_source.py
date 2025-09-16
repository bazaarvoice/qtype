from typing import Any, Tuple

import boto3  # type: ignore[import-untyped]
import pandas as pd
import sqlalchemy
from sqlalchemy import create_engine
from sqlalchemy.exc import SQLAlchemyError

from qtype.base.exceptions import InterpreterError
from qtype.interpreter.auth.generic import auth
from qtype.interpreter.batch.types import BatchConfig, ErrorMode
from qtype.interpreter.batch.utils import reconcile_results_and_errors
from qtype.semantic.model import SQLSource


def to_output_columns(
    df: pd.DataFrame, output_columns: set[str]
) -> pd.DataFrame:
    """Filters the DataFrame to only include specified output columns.

    Args:
        df: The input DataFrame.
        output_columns: A set of column names to retain in the DataFrame.

    Returns:
        A DataFrame containing only the specified output columns.
    """
    if len(df) == 0:
        return df
    missing = output_columns - set(df.columns)
    if missing:
        raise InterpreterError(
            f"SQL Result was missing expected columns: {','.join(missing)}, it has columns: {','.join(df.columns)}"
        )

    return df[[col for col in df.columns if col in output_columns]]


def execute_sql_source(
    step: SQLSource,
    inputs: pd.DataFrame,
    batch_config: BatchConfig,
    **kwargs: dict[Any, Any],
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Executes a SQLSource step to retrieve data from a SQL database.

    Args:
        step: The SQLSource step to execute.

    Returns:
        A tuple containing two DataFrames:
            - The first DataFrame contains the successfully retrieved data.
            - The second DataFrame contains rows that encountered errors with an 'error' column.
    """
    # Create a database engine
    connect_args = {}
    if step.auth:
        with auth(step.auth) as creds:
            if isinstance(creds, boto3.Session):
                connect_args["session"] = creds
    engine = create_engine(step.connection, connect_args=connect_args)

    output_columns = {output.id for output in step.outputs}

    results = []
    errors = []
    step_inputs = {i.id for i in step.inputs}
    for _, row in inputs.iterrows():
        try:
            # Make a dictionary of column_name: value from row
            params = {col: row[col] for col in row.index if col in step_inputs}
            # Execute the query and fetch the results into a DataFrame
            with engine.connect() as connection:
                result = connection.execute(
                    sqlalchemy.text(step.query),
                    parameters=params if len(params) else None,
                )
                df = pd.DataFrame(
                    result.fetchall(), columns=list(result.keys())
                )
            df = to_output_columns(df, output_columns)
            # Augment with all input row columns (fan-out-right)
            df = df.assign(**row.to_dict())
            results.append(df)
        except SQLAlchemyError as e:
            if batch_config.error_mode == ErrorMode.FAIL:
                raise e
            # If there's an error, return an empty DataFrame and the error message
            error_df = pd.DataFrame([{"error": str(e)}])
            errors.append(error_df)

    return reconcile_results_and_errors(results, errors)
