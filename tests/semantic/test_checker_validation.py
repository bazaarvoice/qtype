"""Test semantic validation rules in checker.py."""

from __future__ import annotations

from pathlib import Path

import pytest

from qtype.semantic.checker import QTypeSemanticError
from qtype.semantic.loader import load


@pytest.mark.parametrize(
    "yaml_file,expected_error_fragment",
    [
        (
            "invalid_agent_no_input.qtype.yaml",
            "must have exactly 1 input variable(s), found 0",
        ),
        (
            "invalid_agent_mismatched_types.qtype.yaml",
            "output type must match input type",
        ),
        (
            "invalid_agent_wrong_input_type.qtype.yaml",
            "input must be of type 'text' or 'ChatMessage'",
        ),
        (
            "invalid_prompt_template_no_output.qtype.yaml",
            "must have exactly 1 output variable(s), found 0",
        ),
        (
            "invalid_prompt_template_multiple_outputs.qtype.yaml",
            "must have exactly 1 output variable(s), found 2",
        ),
        (
            "invalid_prompt_template_wrong_output_type.qtype.yaml",
            "output must be of type 'PrimitiveTypeEnum.text'",
        ),
        (
            "invalid_llm_inference_multiple_outputs.qtype.yaml",
            "must have exactly 1 output variable(s), found 2",
        ),
        (
            "invalid_decoder_no_input.qtype.yaml",
            "must have exactly 1 input variable(s), found 0",
        ),
        (
            "invalid_decoder_no_output.qtype.yaml",
            "must have at least 1 output variable(s)",
        ),
        (
            "invalid_sql_source_no_output.qtype.yaml",
            "must have at least 1 output variable(s)",
        ),
        (
            "invalid_document_source_no_output.qtype.yaml",
            "must have exactly 1 output variable(s), found 0",
        ),
        (
            "invalid_document_source_wrong_output_type.qtype.yaml",
            "output must be of type 'RAGDocument'",
        ),
        (
            "invalid_doc_to_text_converter_wrong_input.qtype.yaml",
            "input must be of type 'RAGDocument'",
        ),
        (
            "invalid_document_splitter_wrong_input.qtype.yaml",
            "input must be of type 'RAGDocument'",
        ),
        (
            "invalid_document_splitter_wrong_output.qtype.yaml",
            "output must be of type 'RAGChunk'",
        ),
        (
            "invalid_document_embedder_wrong_input.qtype.yaml",
            "input must be of type 'RAGChunk'",
        ),
        (
            "invalid_index_upsert_wrong_input_type.qtype.yaml",
            "input must be of type 'RAGChunk' or 'RAGDocument'",
        ),
        (
            "invalid_vector_search_no_input.qtype.yaml",
            "must have exactly 1 input variable(s), found 0",
        ),
        (
            "invalid_document_search_wrong_input_type.qtype.yaml",
            "input must be of type 'PrimitiveTypeEnum.text'",
        ),
        (
            "invalid_flow_no_steps.qtype.yaml",
            "must have one or more steps, found 0",
        ),
        (
            "invalid_flow_unfulfilled_input.qtype.yaml",
            "has input variables that are not included in the flow or previous outputs",
        ),
        (
            "invalid_secret_reference_no_manager.qtype.yaml",
            "uses SecretReference but does not have a secret_manager configured",
        ),
        (
            "invalid_secret_manager_wrong_auth_type.qtype.yaml",
            "AWSSecretManager 'my_secret_manager' requires an AWSAuthProvider",
        ),
        (
            "invalid_complete_flow_no_text_output.qtype.yaml",
            "final step 'echo_step' is of type 'Echo' which does not support streaming",
        ),
    ],
)
def test_checker_validation_errors(yaml_file, expected_error_fragment):
    """Test that semantic validation rules are enforced correctly."""
    test_file = Path(__file__).parent / "checker-error-specs" / yaml_file

    with pytest.raises(QTypeSemanticError) as exc_info:
        load(test_file)

    assert expected_error_fragment in str(exc_info.value), (
        f"Expected error fragment '{expected_error_fragment}' not found "
        f"in error message: {exc_info.value}"
    )
