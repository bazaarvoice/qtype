from pydantic import BaseModel

from qtype.base.types import PrimitiveTypeEnum
from qtype.dsl.domain_types import RAGChunk, RAGDocument
from qtype.dsl.linker import QTypeValidationError
from qtype.dsl.model import AWSAuthProvider
from qtype.semantic.model import (
    Decoder,
    DocToTextConverter,
    DocumentEmbedder,
    DocumentSearch,
    DocumentSource,
    DocumentSplitter,
    Flow,
    IndexUpsert,
    LLMInference,
    PromptTemplate,
    SQLSource,
    Step,
    VectorSearch,
)

#
# This file contains rules for the language that are evaluated after
# it is loaded into the semantic representation
#


class FlowHasNoStepsError(QTypeValidationError):
    """Raised when a flow has no steps defined."""

    def __init__(self, flow_id: str):
        super().__init__(f"Flow {flow_id} has no steps defined.")


class QTypeSemanticError(QTypeValidationError):
    """Raised when there's an error during QType semantic validation."""

    pass


# ---- Helper Functions for Common Validation Patterns ----


def _validate_exact_input_count(
    step: Step, expected: int, input_type=None
) -> None:
    """
    Validate a step has exactly the expected number of inputs.

    Args:
        step: The step to validate
        expected: Expected number of inputs
        input_type: Optional expected type for the inputs (PrimitiveTypeEnum or type)

    Raises:
        QTypeSemanticError: If validation fails
    """
    if len(step.inputs) != expected:
        raise QTypeSemanticError(
            (
                f"{step.type} step '{step.id}' must have exactly "
                f"{expected} input variable(s), found {len(step.inputs)}."
            )
        )

    if input_type is not None and len(step.inputs) > 0:
        actual_type = step.inputs[0].type
        if actual_type != input_type:
            type_name = (
                input_type.__name__
                if hasattr(input_type, "__name__")
                else str(input_type)
            )
            raise QTypeSemanticError(
                (
                    f"{step.type} step '{step.id}' input must be of type "
                    f"'{type_name}', found '{actual_type}'."
                )
            )


def _validate_exact_output_count(
    step: Step, expected: int, output_type=None
) -> None:
    """
    Validate a step has exactly the expected number of outputs.

    Args:
        step: The step to validate
        expected: Expected number of outputs
        output_type: Optional expected type for the outputs (PrimitiveTypeEnum or type)

    Raises:
        QTypeSemanticError: If validation fails
    """
    if len(step.outputs) != expected:
        raise QTypeSemanticError(
            (
                f"{step.type} step '{step.id}' must have exactly "
                f"{expected} output variable(s), found {len(step.outputs)}."
            )
        )

    if output_type is not None and len(step.outputs) > 0:
        actual_type = step.outputs[0].type
        if actual_type != output_type:
            type_name = (
                output_type.__name__
                if hasattr(output_type, "__name__")
                else str(output_type)
            )
            raise QTypeSemanticError(
                (
                    f"{step.type} step '{step.id}' output must be of type "
                    f"'{type_name}', found '{actual_type}'."
                )
            )


def _validate_min_output_count(step: Step, minimum: int) -> None:
    """
    Validate a step has at least the minimum number of outputs.

    Args:
        step: The step to validate
        minimum: Minimum number of outputs required

    Raises:
        QTypeSemanticError: If validation fails
    """
    if len(step.outputs) < minimum:
        raise QTypeSemanticError(
            (
                f"{step.type} step '{step.id}' must have at least "
                f"{minimum} output variable(s)."
            )
        )


def _validate_input_output_types_match(
    step: Step, input_type: type, output_type: type
) -> None:
    """
    Validate a step has matching input and output types.

    Args:
        step: The step to validate
        input_type: Expected input type
        output_type: Expected output type

    Raises:
        QTypeSemanticError: If validation fails
    """
    _validate_exact_input_count(step, 1, input_type)
    _validate_exact_output_count(step, 1, output_type)


def _validate_prompt_template(t: PromptTemplate) -> None:
    """Validate PromptTemplate has exactly one text output."""
    _validate_exact_output_count(t, 1, PrimitiveTypeEnum.text)


def _validate_aws_auth(a: AWSAuthProvider) -> None:
    """Validate AWS authentication configuration."""
    # At least one auth method must be specified
    has_keys = a.access_key_id and a.secret_access_key
    has_profile = a.profile_name
    has_role = a.role_arn

    if not (has_keys or has_profile or has_role):
        raise ValueError(
            "AWSAuthProvider must specify at least one authentication method: "
            "access keys, profile name, or role ARN."
        )

    # If assuming a role, need either keys or profile for base credentials
    if has_role and not (has_keys or has_profile):
        raise ValueError(
            "Role assumption requires base credentials (access keys or profile)."
        )


def _validate_llm_inference(step: LLMInference) -> None:
    """Validate LLMInference step has exactly one text output."""
    _validate_exact_output_count(step, 1, PrimitiveTypeEnum.text)


def _validate_decoder(step: Decoder) -> None:
    """Validate Decoder step has exactly one text input and at least one output."""
    _validate_exact_input_count(step, 1, PrimitiveTypeEnum.text)
    _validate_min_output_count(step, 1)


def _validate_sql_source(step: SQLSource) -> None:
    """Validate SQLSource has output variables defined."""
    _validate_min_output_count(step, 1)


def _validate_document_source(step: DocumentSource) -> None:
    """Validate DocumentSource has exactly one RAGDocument output."""
    _validate_exact_output_count(step, 1, RAGDocument)


def _validate_doc_to_text_converter(step: DocToTextConverter) -> None:
    """Validate DocToTextConverter has exactly one RAGDocument input and output."""
    _validate_input_output_types_match(step, RAGDocument, RAGDocument)


def _validate_document_splitter(step: DocumentSplitter) -> None:
    """Validate DocumentSplitter has exactly one RAGDocument input and one RAGChunk output."""
    _validate_input_output_types_match(step, RAGDocument, RAGChunk)


def _validate_document_embedder(step: DocumentEmbedder) -> None:
    """Validate DocumentEmbedder has exactly one RAGChunk input and output."""
    _validate_input_output_types_match(step, RAGChunk, RAGChunk)


def _validate_index_upsert(step: IndexUpsert) -> None:
    """Validate IndexUpsert has exactly one input of type RAGChunk or RAGDocument."""
    _validate_exact_input_count(step, 1)
    input_type = step.inputs[0].type
    if input_type not in (RAGChunk, RAGDocument):
        raise QTypeSemanticError(
            (
                f"IndexUpsert step '{step.id}' input must be of type "
                f"'RAGChunk' or 'RAGDocument', found '{input_type}'."
            )
        )


def _validate_vector_search(step: VectorSearch) -> None:
    """Validate VectorSearch has exactly one text input for the query."""
    _validate_exact_input_count(step, 1, PrimitiveTypeEnum.text)


def _validate_document_search(step: DocumentSearch) -> None:
    """Validate DocumentSearch has exactly one text input for the query."""
    _validate_exact_input_count(step, 1, PrimitiveTypeEnum.text)


def _validate_flow(flow: Flow) -> None:
    """Validate Flow has more than one step."""
    if len(flow.steps) < 1:
        raise QTypeSemanticError(
            f"Flow '{flow.id}' must have one or more steps, found {len(flow.steps)}."
        )


# Mapping of types to their validation functions
_VALIDATORS = {
    PromptTemplate: _validate_prompt_template,
    AWSAuthProvider: _validate_aws_auth,
    LLMInference: _validate_llm_inference,
    Decoder: _validate_decoder,
    SQLSource: _validate_sql_source,
    DocumentSource: _validate_document_source,
    DocToTextConverter: _validate_doc_to_text_converter,
    DocumentSplitter: _validate_document_splitter,
    DocumentEmbedder: _validate_document_embedder,
    IndexUpsert: _validate_index_upsert,
    VectorSearch: _validate_vector_search,
    DocumentSearch: _validate_document_search,
    Flow: _validate_flow,
}


def check(model: BaseModel) -> None:
    """
    Recursively validate a pydantic BaseModel and all its fields.

    For each field, if its type has a registered validator, call that validator.
    Then recursively validate the field value itself.

    Args:
        model: The pydantic BaseModel instance to validate

    Raises:
        QTypeSemanticError: If any validation rules are violated
    """
    # Check if this model type has a validator
    model_type = type(model)
    if model_type in _VALIDATORS:
        _VALIDATORS[model_type](model)

    # Recursively validate all fields
    for field_name, field_value in model:
        if field_value is None:
            continue

        # Handle lists
        if isinstance(field_value, list):
            for item in field_value:
                if isinstance(item, BaseModel):
                    check(item)
        # Handle dicts
        elif isinstance(field_value, dict):
            for value in field_value.values():
                if isinstance(value, BaseModel):
                    check(value)
        # Handle BaseModel instances
        elif isinstance(field_value, BaseModel):
            check(field_value)
