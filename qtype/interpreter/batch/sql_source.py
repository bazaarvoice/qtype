from typing import Tuple

import boto3
import pandas as pd
import sqlalchemy
from sqlalchemy import create_engine
from sqlalchemy.exc import SQLAlchemyError

from qtype.interpreter.auth.generic import auth
from qtype.semantic.model import SQLSource


def execute_sql_source(
    step: SQLSource,
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
                connect_args["boto3_session"] = creds
    engine = create_engine(step.connection, connect_args=connect_args)

    try:
        # Execute the query and fetch the results into a DataFrame
        with engine.connect() as connection:
            result = connection.execute(sqlalchemy.text(step.query))
            df = pd.DataFrame(result.fetchall(), columns=list(result.keys()))
        return (
            df,
            pd.DataFrame(),
        )  # No errors, return empty DataFrame for errors
    except SQLAlchemyError as e:
        # If there's an error, return an empty DataFrame and the error message
        error_df = pd.DataFrame([{"error": str(e)}])
        return pd.DataFrame(), error_df
