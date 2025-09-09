from turtle import pd
from typing import Tuple

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
    import pandas as pd
    import sqlalchemy
    from sqlalchemy import create_engine
    from sqlalchemy.exc import SQLAlchemyError

    # Create a database engine
    if step.auth:
        # If authentication details are provided, use them to create the engine
        engine = create_engine(
            step.connection,
            connect_args=step.auth,
        )
    engine = create_engine(step.connection)

    try:
        # Execute the query and fetch the results into a DataFrame
        with engine.connect() as connection:
            result = connection.execute(sqlalchemy.text(step.query))
            df = pd.DataFrame(result.fetchall(), columns=result.keys())
        return (
            df,
            pd.DataFrame(),
        )  # No errors, return empty DataFrame for errors
    except SQLAlchemyError as e:
        # If there's an error, return an empty DataFrame and the error message
        error_df = pd.DataFrame([{"error": str(e)}])
        return pd.DataFrame(), error_df
