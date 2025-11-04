from typing import AsyncIterator

import boto3  # type: ignore[import-untyped]
import pandas as pd
import sqlalchemy
from sqlalchemy import create_engine
from sqlalchemy.exc import SQLAlchemyError

from qtype.interpreter.auth.generic import auth
from qtype.interpreter.base.base_step_executor import StepExecutor
from qtype.interpreter.base.executor_context import ExecutorContext
from qtype.interpreter.types import FlowMessage
from qtype.semantic.model import SQLSource


class SQLSourceExecutor(StepExecutor):
    """Executor for SQLSource steps."""

    def __init__(
        self, step: SQLSource, context: ExecutorContext, **dependencies
    ):
        super().__init__(step, context, **dependencies)
        if not isinstance(step, SQLSource):
            raise ValueError(
                "SQLSourceExecutor can only execute SQLSource steps."
            )
        self.step: SQLSource = step

    async def process_message(
        self,
        message: FlowMessage,
    ) -> AsyncIterator[FlowMessage]:
        """Process a single FlowMessage for the SQLSource step.

        Args:
            message: The FlowMessage to process.
        Yields:
            FlowMessages with the results of SQL query execution.
        """
        # Create a database engine - resolve connection string if it's a SecretReference
        connection_string = self._resolve_secret(self.step.connection)
        connect_args = {}
        if self.step.auth:
            with auth(self.step.auth) as creds:
                if isinstance(creds, boto3.Session):
                    connect_args["session"] = creds
        engine = create_engine(connection_string, connect_args=connect_args)

        output_columns = {output.id for output in self.step.outputs}
        step_inputs = {i.id for i in self.step.inputs}

        try:
            # Make a dictionary of column_name: value from message variables
            params = {
                col: message.variables.get(col)
                for col in step_inputs
                if col in message.variables
            }

            await self.stream_emitter.status(
                f"Executing SQL query with params: {params}",
            )

            # Execute the query and fetch the results into a DataFrame
            with engine.connect() as connection:
                result = connection.execute(
                    sqlalchemy.text(self.step.query),
                    parameters=params if params else None,
                )
                df = pd.DataFrame(
                    result.fetchall(), columns=list(result.keys())
                )

            # Confirm the outputs exist in the dataframe
            columns = set(df.columns)
            missing_columns = output_columns - columns
            if missing_columns:
                raise ValueError(
                    (
                        f"SQL Result was missing expected columns: "
                        f"{', '.join(missing_columns)}, it has columns: "
                        f"{', '.join(columns)}"
                    )
                )

            # Emit one message per result row
            for _, row in df.iterrows():
                # Create a dict with only the output columns
                row_dict = {
                    str(k): v
                    for k, v in row.to_dict().items()
                    if str(k) in output_columns
                }
                # Merge with original message variables
                yield message.copy_with_variables(new_variables=row_dict)

            await self.stream_emitter.status(
                f"Emitted {len(df)} rows from SQL query"
            )

        except SQLAlchemyError as e:
            # Emit error event to stream so frontend can display it
            await self.stream_emitter.error(str(e))
            # Set error on the message and yield it
            message.set_error(self.step.id, e)
            yield message
