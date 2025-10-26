from __future__ import annotations

from typing import Any, Tuple

import pandas as pd

from qtype.base.exceptions import InterpreterError
from qtype.base.types import BatchConfig
from qtype.dsl.domain_types import RAGDocument
from qtype.interpreter.batch.types import ErrorMode
from qtype.interpreter.batch.utils import reconcile_results_and_errors
from qtype.interpreter.conversions import to_llama_document, to_vector_store
from qtype.semantic.model import IndexUpsert


def execute_index_upsert(
    step: IndexUpsert,
    inputs: pd.DataFrame,
    batch_config: BatchConfig,
    **kwargs: dict[Any, Any],
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Executes an IndexUpsert step to add documents to a vector store.

    Args:
        step: The IndexUpsert step to execute.
        inputs: Input DataFrame containing RAGDocument data to upsert.
        batch_config: Configuration for batch processing.
        **kwargs: Additional keyword arguments.

    Returns:
        A tuple containing two DataFrames:
            - The first DataFrame contains success indicators with document IDs.
            - The second DataFrame contains rows that encountered errors with an 'error' column.
    """
    # Validate that we have exactly one output variable
    if len(step.outputs) != 1:
        raise InterpreterError(
            f"IndexUpsert must have exactly one output variable, got {len(step.outputs)}."
        )
    output_column_name = step.outputs[0].id

    # Validate that we have exactly one input variable
    if len(step.inputs) != 1:
        raise InterpreterError(
            f"IndexUpsert must have exactly one input variable, got {len(step.inputs)}."
        )
    input_column_name = step.inputs[0].id

    # Get the vector store
    try:
        vector_store = to_vector_store(step.index)
    except Exception as e:
        if batch_config.error_mode == ErrorMode.FAIL:
            raise InterpreterError(
                f"Failed to initialize vector store for index '{step.index.id}': {e}"
            ) from e
        # If we can't initialize the vector store, all rows fail
        error_df = pd.DataFrame(
            [{"error": f"Failed to initialize vector store: {e}"}]
            * len(inputs)
        )
        return pd.DataFrame(), error_df

    results = []
    errors = []

    # Process documents in batches
    batch_size = batch_config.batch_size
    for batch_start in range(0, len(inputs), batch_size):
        batch_end = min(batch_start + batch_size, len(inputs))
        batch_df = inputs.iloc[batch_start:batch_end].copy()

        try:
            # Convert RAGDocuments to LlamaDocuments
            rag_documents = batch_df[input_column_name].tolist()
            llama_documents = []

            for rag_doc in rag_documents:
                if not isinstance(rag_doc, RAGDocument):
                    raise InterpreterError(
                        f"Expected RAGDocument, got {type(rag_doc).__name__}"
                    )
                llama_documents.append(to_llama_document(rag_doc))

            # Add documents to the vector store
            # vector_store.add returns document IDs
            doc_ids = vector_store.add(llama_documents)

            # Create result DataFrame with document IDs
            batch_df[output_column_name] = doc_ids
            results.append(batch_df)

        except Exception as e:
            if batch_config.error_mode == ErrorMode.FAIL:
                raise InterpreterError(
                    f"Failed to upsert documents to index '{step.index.id}': {e}"
                ) from e

            # If there's an error, add error rows for the entire batch
            error_rows = []
            for _ in range(len(batch_df)):
                error_rows.append({"error": str(e)})
            error_df = pd.DataFrame(error_rows)
            errors.append(error_df)

    return reconcile_results_and_errors(results, errors)
