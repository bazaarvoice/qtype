from typing import Any

from pydantic import BaseModel

from qtype.base.exceptions import SemanticError
from qtype.base.types import PrimitiveTypeEnum
from qtype.dsl.domain_types import ChatMessage, RAGChunk, RAGDocument
from qtype.dsl.linker import QTypeValidationError
from qtype.dsl.model import AWSAuthProvider
from qtype.semantic.model import (
    Agent,
    Application,
    Decoder,
    DocToTextConverter,
    DocumentEmbedder,
    DocumentSearch,
    DocumentSource,
    DocumentSplitter,
    Echo,
    FieldExtractor,
    Flow,
    IndexUpsert,
    LLMInference,
    PromptTemplate,
    SecretReference,
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


# Alias for backward compatibility and semantic clarity
QTypeSemanticError = SemanticError


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

    _validate_exact_output_count(step, 1)
    ALLOWED_TYPES = {PrimitiveTypeEnum.text, ChatMessage}
    if step.outputs[0].type not in ALLOWED_TYPES:
        raise QTypeSemanticError(
            (
                f"LLMInference step '{step.id}' output must be of type "
                f"'PrimitiveTypeEnum.text' or 'ChatMessage', found "
                f"'{step.outputs[0].type}'."
            )
        )


def _validate_agent(step: Agent) -> None:
    """Validate Agent step has exactly one input and output with matching types.

    Agent constraints:
    - Must have exactly one input (text or ChatMessage)
    - Must have exactly one output
    - Output type must match input type
    """
    # Validate exactly one input
    _validate_exact_input_count(step, 1)

    # Validate exactly one output
    _validate_exact_output_count(step, 1)

    # Validate input type is text or ChatMessage
    input_type = step.inputs[0].type
    output_type = step.outputs[0].type

    ALLOWED_TYPES = {PrimitiveTypeEnum.text, ChatMessage}
    if input_type not in ALLOWED_TYPES:
        raise QTypeSemanticError(
            (
                f"Agent step '{step.id}' input must be of type "
                f"'text' or 'ChatMessage', found '{input_type}'."
            )
        )

    # Validate output type matches input type
    if input_type != output_type:
        raise QTypeSemanticError(
            (
                f"Agent step '{step.id}' output type must match input type. "
                f"Input type: '{input_type}', Output type: '{output_type}'."
            )
        )


def _validate_decoder(step: Decoder) -> None:
    """Validate Decoder step has exactly one text input and at least one output."""
    _validate_exact_input_count(step, 1, PrimitiveTypeEnum.text)
    _validate_min_output_count(step, 1)


def _validate_echo(step: Echo) -> None:
    """
    Validate Echo step has matching input and output variable IDs.

    The inputs and outputs must contain the same set of variable IDs,
    though they can be in different order.

    Args:
        step: The Echo step to validate

    Raises:
        QTypeSemanticError: If inputs and outputs don't match
    """
    input_ids = {var.id for var in step.inputs}
    output_ids = {var.id for var in step.outputs}

    if input_ids != output_ids:
        missing_in_outputs = input_ids - output_ids
        extra_in_outputs = output_ids - input_ids

        error_msg = (
            f"Echo step '{step.id}' must have the same variable IDs "
            f"in inputs and outputs (order can differ)."
        )
        if missing_in_outputs:
            error_msg += f" Missing in outputs: {sorted(missing_in_outputs)}."
        if extra_in_outputs:
            error_msg += f" Extra in outputs: {sorted(extra_in_outputs)}."

        raise QTypeSemanticError(error_msg)


def _validate_field_extractor(step: FieldExtractor) -> None:
    """
    Validate FieldExtractor step has exactly one input and one output.

    Args:
        step: The FieldExtractor step to validate

    Raises:
        QTypeSemanticError: If validation fails
    """
    _validate_exact_input_count(step, 1)
    _validate_exact_output_count(step, 1)

    # Validate json_path is not empty
    if not step.json_path or not step.json_path.strip():
        raise QTypeSemanticError(
            f"FieldExtractor step '{step.id}' must have a non-empty json_path."
        )


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
    """Validate VectorSearch has exactly one text input and one list[RAGSearchResult] output."""
    from qtype.dsl.model import ListType

    _validate_exact_input_count(step, 1, PrimitiveTypeEnum.text)
    _validate_exact_output_count(
        step, 1, ListType(element_type="RAGSearchResult")
    )


def _validate_document_search(step: DocumentSearch) -> None:
    """Validate DocumentSearch has exactly one text input for the query."""
    _validate_exact_input_count(step, 1, PrimitiveTypeEnum.text)


def _validate_flow(flow: Flow) -> None:
    """Validate Flow has more than one step."""
    if len(flow.steps) < 1:
        raise QTypeSemanticError(
            f"Flow '{flow.id}' must have one or more steps, found {len(flow.steps)}."
        )

    # Crawl the steps and identify all input and output variables.
    fullfilled_variables = {i.id for i in flow.inputs}

    for step in flow.steps:
        step_input_ids = {i.id for i in step.inputs}
        not_fulfilled = step_input_ids - fullfilled_variables
        if not_fulfilled:
            raise QTypeSemanticError(
                f"Flow '{flow.id}' step '{step.id}' has input variables that are not included in the flow or previous outputs: {not_fulfilled}."
            )
        fullfilled_variables = {
            i.id for i in step.outputs
        } | fullfilled_variables

    if flow.interface:
        if flow.interface.type == "Conversational":
            # If it's a chat interface, there must be at least one ChatMessage input and one ChatMessage output
            # in the spec. All non-ChatMessage inputs must be specified in the session_inputs part of the flowinterface.

            # ensure there is one chatmessage input
            chat_message_inputs = {
                i.id for i in flow.inputs if i.type == ChatMessage
            }
            if not len(chat_message_inputs):
                raise QTypeSemanticError(
                    f"Flow {flow.id} has a Conversational interface but no ChatMessage inputs."
                )
            if len(chat_message_inputs) > 1:
                raise QTypeSemanticError(
                    f"Flow {flow.id} has a Conversational interface but multiple ChatMessage inputs."
                )

            # ensure non chatmessage inputs are listed as variables in session
            non_chat_message_inputs = {
                i.id for i in flow.inputs
            } - chat_message_inputs
            variables_in_session = {
                i.id for i in flow.interface.session_inputs
            }
            not_in_session = non_chat_message_inputs - variables_in_session
            if not_in_session:
                not_in_session_str = ",".join(not_in_session)
                raise QTypeSemanticError(
                    f"Flow {flow.id} is Conversational so {not_in_session_str} inputs must be listed in session_inputs"
                )

            # ensure there is one chat message output
            chat_message_outputs = {
                i.id for i in flow.outputs if i.type == ChatMessage
            }
            if len(chat_message_outputs) != 1:
                raise QTypeSemanticError(
                    f"Flow {flow.id} has a Conversational interface so it must have one and only one ChatMessage output."
                )

        elif flow.interface.type == "Complete":
            # ensure there is one input and it is text
            prompt_input = [
                i for i in flow.inputs if i.type == PrimitiveTypeEnum.text
            ]
            if len(prompt_input) != 1:
                raise QTypeSemanticError(
                    f'Flow has a Complete interface but {len(prompt_input)} prompt inputs -- there should be one input with type text and id "prompt"'
                )

            # stream if there is at least one output of type text. All other outputs should be returned by the call but not streamed.
            text_outputs = {
                i.id for i in flow.outputs if i.type == PrimitiveTypeEnum.text
            }
            if len(text_outputs) != 1:
                raise QTypeSemanticError(
                    f"Flow {flow.id} has a Complete interface but {len(text_outputs)} text outputs -- there should be 1."
                )


def _has_secret_reference(obj: Any) -> bool:
    """
    Recursively check if an object contains any SecretReference instances.

    This function traverses Pydantic models, lists, and dictionaries to find
    any SecretReference instances that require a secret manager for resolution.

    Args:
        obj: Object to check - can be a Pydantic BaseModel, list, dict,
            SecretReference, or any other Python object

    Returns:
        True if SecretReference is found anywhere in the object graph,
        False otherwise

    Examples:
        >>> from qtype.semantic.model import SecretReference
        >>> _has_secret_reference("plain string")
        False
        >>> _has_secret_reference(SecretReference(secret_name="my-secret"))
        True
        >>> _has_secret_reference({"key": SecretReference(secret_name="s")})
        True
    """
    # Direct check - most common case
    if isinstance(obj, SecretReference):
        return True

    # Check Pydantic models by iterating over field values
    if isinstance(obj, BaseModel):
        for field_name, field_value in obj:
            if _has_secret_reference(field_value):
                return True

    # Check lists
    elif isinstance(obj, list):
        for item in obj:
            if _has_secret_reference(item):
                return True

    # Check dictionaries
    elif isinstance(obj, dict):
        for value in obj.values():
            if _has_secret_reference(value):
                return True

    return False


def _validate_application(application: Application) -> None:
    """
    Validate Application configuration.

    Args:
        application: The Application to validate

    Raises:
        QTypeSemanticError: If SecretReference is used but
            secret_manager is not configured, or if secret_manager
            configuration is invalid
    """
    if application.secret_manager is None:
        # Check if any SecretReference is used in the application
        if _has_secret_reference(application):
            raise QTypeSemanticError(
                (
                    f"Application '{application.id}' uses SecretReference "
                    "but does not have a secret_manager configured. "
                    "Please add a secret_manager to the application."
                )
            )
    else:
        # Validate secret_manager configuration
        from qtype.semantic.model import AWSAuthProvider, AWSSecretManager

        secret_mgr = application.secret_manager

        # For AWSSecretManager, verify auth is AWSAuthProvider
        # (linker ensures the reference exists, we just check the type)
        if isinstance(secret_mgr, AWSSecretManager):
            auth_provider = secret_mgr.auth
            if not isinstance(auth_provider, AWSAuthProvider):
                raise QTypeSemanticError(
                    (
                        f"AWSSecretManager '{secret_mgr.id}' requires an "
                        f"AWSAuthProvider but references '{auth_provider.id}' "
                        f"which is of type '{type(auth_provider).__name__}'"
                    )
                )


# Mapping of types to their validation functions
_VALIDATORS = {
    Agent: _validate_agent,
    Application: _validate_application,
    PromptTemplate: _validate_prompt_template,
    AWSAuthProvider: _validate_aws_auth,
    LLMInference: _validate_llm_inference,
    Decoder: _validate_decoder,
    Echo: _validate_echo,
    FieldExtractor: _validate_field_extractor,
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
