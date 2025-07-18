import logging
import string
from typing import Any

from qtype.interpreter.exceptions import InterpreterError
from qtype.semantic.model import PromptTemplate, Variable

logger = logging.getLogger(__name__)


def get_format_arguments(format_string: str) -> set[str]:
    formatter = string.Formatter()
    arguments = []
    for literal_text, field_name, format_spec, conversion in formatter.parse(
        format_string
    ):
        if field_name:
            arguments.append(field_name)
    return set(arguments)


def execute(step: PromptTemplate, **kwargs: dict[str, Any]) -> list[Variable]:
    """Execute a prompt template step.

    Args:
        step: The prompt template step to execute.
        **kwargs: Additional keyword arguments.
    """

    logger.debug(
        f"Executing prompt template step: {step.id} with kwargs: {kwargs}"
    )

    format_args = get_format_arguments(step.template)
    input_map = {
        var.id: var.value
        for var in step.inputs
        if var.is_set() and var.id in format_args
    }
    missing = format_args - input_map.keys()
    if missing:
        raise InterpreterError(
            f"The following fields are in the prompt template but not in the inputs: {missing}"
        )
    # Drop inputs that are not in format_args
    result = step.template.format(**input_map)

    if len(step.outputs) != 1:
        raise InterpreterError(
            f"PromptTemplate step {step.id} must have exactly one output variable."
        )
    step.outputs[0].value = result

    return step.outputs  # type: ignore[return-value]
