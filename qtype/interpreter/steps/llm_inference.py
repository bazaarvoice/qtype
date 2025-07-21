import logging

from llama_index.core.llms import LLM
from llama_index.llms.bedrock_converse import BedrockConverse

from qtype.interpreter.exceptions import InterpreterError
from qtype.semantic.model import LLMInference, Model, Variable

logger = logging.getLogger(__name__)


# TODO: implement a cache so we're not creating a new LLM instance every time?
def to_llm(model: Model, system_prompt: str | None) -> LLM:
    """Convert a qtype Model to a LlamaIndex Model."""
    # Note only bedrock working for now. TODO: add support for other providers
    # Maybe support arbitrary LLMs llms that LLAmaIndex supports?
    if model.provider in {"bedrock", "amazon_bedrock", "aws", "aws-bedrock"}:
        # BedrockConverse requires a model_id and system_prompt
        # Inference params can be passed as additional kwargs
        return BedrockConverse(
            model=model.model_id if model.model_id else model.id,
            system_prompt=system_prompt,
            **(model.inference_params if model.inference_params else {}),
        )
    else:
        raise InterpreterError(
            f"Unsupported model provider: {model.provider}. Only 'bedrock' is currently supported."
        )


def execute(
    li: LLMInference,
) -> list[Variable]:
    """Execute a LLM inference step.

    Args:
        li: The LLM inference step to execute.
        **kwargs: Additional keyword arguments.
    """
    logger.debug(f"Executing LLM inference step: {li.id}")

    if len(li.outputs) != 1:
        raise InterpreterError(
            "LLMInference step must have exactly one output variable."
        )
    output_variable = li.outputs[0]

    # TODO: Add Memory
    # TODO: Add Chat functionality
    if len(li.inputs) != 1:
        raise InterpreterError(
            "LLMInference step must have exactly one input variable."
        )

    model = to_llm(li.model, li.system_message)
    input = li.inputs[0].value
    if not isinstance(input, str):
        logger.warning(
            f"Input to LLMInference step {li.id} is not a string, converting: {input}"
        )
        input = str(input)

    result = model.complete(prompt=input)
    output_variable.value = result.text

    return li.outputs  # type: ignore[return-value]
