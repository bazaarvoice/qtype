"""Converters between DataFrames and FlowMessages."""

from __future__ import annotations

import pandas as pd
from pydantic import BaseModel

from qtype.interpreter.types import FlowMessage, Session
from qtype.semantic.model import Flow


def dataframe_to_flow_messages(
    df: pd.DataFrame, session: Session
) -> list[FlowMessage]:
    """
    Convert a DataFrame to a list of FlowMessages.

    Each row in the DataFrame becomes a FlowMessage with the same session.

    Args:
        df: DataFrame where each row represents one set of inputs
        session: Session object to use for all messages

    Returns:
        List of FlowMessages, one per DataFrame row
    """
    messages = []
    for _, row in df.iterrows():
        variables = row.to_dict()
        messages.append(FlowMessage(session=session, variables=variables))
    return messages


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
    from typing import Any

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
