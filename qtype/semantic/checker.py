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
    VectorSearch,
)

#
# This file contains rules for the lanugage that are evaluated after it is loaded into the semantic representation
#


class FlowHasNoStepsError(QTypeValidationError):
    """Raised when a flow has no steps defined."""

    def __init__(self, flow_id: str):
        super().__init__(f"Flow {flow_id} has no steps defined.")


class QTypeSemanticError(QTypeValidationError):
    """Raised when there's an error during QType semantic validation."""

    pass


def _validate_prompt_template(t: PromptTemplate) -> None:
    if len(t.outputs) != 1:
        raise QTypeSemanticError(
            f"PromptTemplate {t.id} must have exactly one output, found {len(t.outputs)}."
        )
    if t.outputs[0].type != PrimitiveTypeEnum.text:
        raise QTypeSemanticError(
            f"PromptTemplate {t.id} output must be of type 'text', found {t.outputs[0].type}."
        )


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
    if len(step.outputs) != 1:
        raise QTypeSemanticError(
            f"LLMInference step '{step.id}' must have exactly one output variable, found {len(step.outputs)}."
        )
    if step.outputs[0].type != PrimitiveTypeEnum.text:
        raise QTypeSemanticError(
            f"LLMInference step '{step.id}' output must be of type 'text', found '{step.outputs[0].type}'."
        )


def _validate_decoder(step: Decoder) -> None:
    """Validate Decoder step has exactly one text input and at least one output."""
    if len(step.inputs) != 1:
        raise QTypeSemanticError(
            f"Decoder step '{step.id}' must have exactly one input variable of type 'text'. Found: {step.inputs}"
        )
    if step.inputs[0].type != PrimitiveTypeEnum.text:
        raise QTypeSemanticError(
            f"Decoder step '{step.id}' input must be of type 'text', found '{step.inputs[0].type}'."
        )
    if len(step.outputs) == 0:
        raise QTypeSemanticError(
            f"Decoder step '{step.id}' must have at least one output variable."
        )


def _validate_sql_source(step: SQLSource) -> None:
    """Validate SQLSource has output variables defined."""
    if len(step.outputs) == 0:
        raise QTypeSemanticError(
            f"SQLSource step '{step.id}' must define output variables that match the result columns."
        )


def _validate_document_source(step: DocumentSource) -> None:
    """Validate DocumentSource has exactly one RAGDocument output."""
    if len(step.outputs) != 1:
        raise QTypeSemanticError(
            f"DocumentSource step '{step.id}' must have exactly one output variable, found {len(step.outputs)}."
        )
    if step.outputs[0].type != RAGDocument:
        raise QTypeSemanticError(
            f"DocumentSource step '{step.id}' output must be of type 'RAGDocument', found '{step.outputs[0].type}'."
        )


def _validate_doc_to_text_converter(step: DocToTextConverter) -> None:
    """Validate DocToTextConverter has exactly one RAGDocument input and output."""
    if len(step.inputs) != 1:
        raise QTypeSemanticError(
            f"DocToTextConverter step '{step.id}' must have exactly one input variable, found {len(step.inputs)}."
        )
    if step.inputs[0].type != RAGDocument:
        raise QTypeSemanticError(
            f"DocToTextConverter step '{step.id}' input must be of type 'RAGDocument', found '{step.inputs[0].type}'."
        )
    if len(step.outputs) != 1:
        raise QTypeSemanticError(
            f"DocToTextConverter step '{step.id}' must have exactly one output variable, found {len(step.outputs)}."
        )
    if step.outputs[0].type != RAGDocument:
        raise QTypeSemanticError(
            f"DocToTextConverter step '{step.id}' output must be of type 'RAGDocument', found '{step.outputs[0].type}'."
        )


def _validate_document_splitter(step: DocumentSplitter) -> None:
    """Validate DocumentSplitter has exactly one RAGDocument input and one RAGChunk output."""
    if len(step.inputs) != 1:
        raise QTypeSemanticError(
            f"DocumentSplitter step '{step.id}' must have exactly one input variable, found {len(step.inputs)}."
        )
    if step.inputs[0].type != RAGDocument:
        raise QTypeSemanticError(
            f"DocumentSplitter step '{step.id}' input must be of type 'RAGDocument', found '{step.inputs[0].type}'."
        )
    if len(step.outputs) != 1:
        raise QTypeSemanticError(
            f"DocumentSplitter step '{step.id}' must have exactly one output variable, found {len(step.outputs)}."
        )
    if step.outputs[0].type != RAGChunk:
        raise QTypeSemanticError(
            f"DocumentSplitter step '{step.id}' output must be of type 'RAGChunk', found '{step.outputs[0].type}'."
        )


def _validate_document_embedder(step: DocumentEmbedder) -> None:
    """Validate DocumentEmbedder has exactly one RAGChunk input and output."""
    if len(step.inputs) != 1:
        raise QTypeSemanticError(
            f"DocumentEmbedder step '{step.id}' must have exactly one input variable, found {len(step.inputs)}."
        )
    if step.inputs[0].type != RAGChunk:
        raise QTypeSemanticError(
            f"DocumentEmbedder step '{step.id}' input must be of type 'RAGChunk', found '{step.inputs[0].type}'."
        )
    if len(step.outputs) != 1:
        raise QTypeSemanticError(
            f"DocumentEmbedder step '{step.id}' must have exactly one output variable, found {len(step.outputs)}."
        )
    if step.outputs[0].type != RAGChunk:
        raise QTypeSemanticError(
            f"DocumentEmbedder step '{step.id}' output must be of type 'RAGChunk', found '{step.outputs[0].type}'."
        )


def _validate_index_upsert(step: IndexUpsert) -> None:
    """Validate IndexUpsert has exactly one input of type RAGChunk or RAGDocument."""
    if len(step.inputs) != 1:
        raise QTypeSemanticError(
            f"IndexUpsert step '{step.id}' must have exactly one input variable, found {len(step.inputs)}."
        )
    input_type = step.inputs[0].type
    if input_type not in (RAGChunk, RAGDocument):
        raise QTypeSemanticError(
            f"IndexUpsert step '{step.id}' input must be of type 'RAGChunk' or 'RAGDocument', found '{input_type}'."
        )


def _validate_vector_search(step: VectorSearch) -> None:
    """Validate VectorSearch has exactly one text input for the query."""
    if len(step.inputs) != 1:
        raise QTypeSemanticError(
            f"VectorSearch step '{step.id}' must have exactly one text input variable for the query, found {len(step.inputs)}."
        )
    if step.inputs[0].type != PrimitiveTypeEnum.text:
        raise QTypeSemanticError(
            f"VectorSearch step '{step.id}' input must be of type 'text', found '{step.inputs[0].type}'."
        )


def _validate_document_search(step: DocumentSearch) -> None:
    """Validate DocumentSearch has exactly one text input for the query."""
    if len(step.inputs) != 1:
        raise QTypeSemanticError(
            f"DocumentSearch step '{step.id}' must have exactly one text input variable for the query, found {len(step.inputs)}."
        )
    if step.inputs[0].type != PrimitiveTypeEnum.text:
        raise QTypeSemanticError(
            f"DocumentSearch step '{step.id}' input must be of type 'text', found '{step.inputs[0].type}'."
        )


def _validate_flow(flow: Flow) -> None:
    """Validate Flow has more than one step."""
    if len(flow.steps) <= 1:
        raise QTypeSemanticError(
            f"Flow '{flow.id}' must have more than one step, found {len(flow.steps)}."
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
