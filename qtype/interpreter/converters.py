"""Converters between DataFrames and FlowMessages."""

from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Any, cast

import pandas as pd
from pydantic import BaseModel

from qtype.interpreter.types import FlowMessage, Session
from qtype.semantic.model import Flow


async def dataframe_to_flow_messages(
    df: pd.DataFrame, session: Session
) -> AsyncIterator[FlowMessage]:
    """
    Convert a DataFrame to an async generator of FlowMessages.

    Each row in the DataFrame becomes a FlowMessage with the same session.

    Args:
        df: DataFrame where each row represents one set of inputs
        session: Session object to use for all messages

    Yields:
        FlowMessages, one per DataFrame row
    """
    # Use to_dict with orient='records' - much faster than iterrows
    # This returns a list of dicts directly without Series overhead
    records = cast(list[dict[str, Any]], df.to_dict(orient="records"))

    for record in records:
        yield FlowMessage(session=session, variables=record)


def flow_messages_to_dataframe(
    messages: list[FlowMessage], flow: Flow
) -> pd.DataFrame:
    """
    Convert a list of FlowMessages to a DataFrame.

    Extracts output variables from each message based on the flow's outputs.

    Args:
        messages: List of FlowMessages with results
        flow: Flow definition containing output variable specifications

    Returns:
        DataFrame with one row per message, columns for each output variable
    """
    results = []
    for idx, message in enumerate(messages):
        row_data: dict[str, Any] = {"row": idx}

        # Extract output variables
        for var in flow.outputs:
            if var.id in message.variables:
                value = message.variables[var.id]
                if isinstance(value, BaseModel):
                    value = value.model_dump()
                row_data[var.id] = value
            else:
                row_data[var.id] = None

        # Include error if present
        if message.is_failed():
            row_data["error"] = (
                message.error.error_message
                if message.error
                else "Unknown error"
            )
        else:
            row_data["error"] = None

        results.append(row_data)

    return pd.DataFrame(results)
