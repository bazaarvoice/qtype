import json
import xml.etree.ElementTree as ET
from typing import Any

from qtype.dsl.model import DecoderFormat
from qtype.semantic.model import Decoder, Variable


def parse_json(input: str) -> dict[str, Any]:
    """Parse a JSON string into a Python object."""
    try:
        cleaned_response = input.strip()
        if cleaned_response.startswith("```json"):
            cleaned_response = cleaned_response[7:]
        if cleaned_response.endswith("```"):
            cleaned_response = cleaned_response[:-3]
        cleaned_response = cleaned_response.strip()

        # Parse the JSON
        parsed = json.loads(cleaned_response)
        if not isinstance(parsed, dict):
            raise ValueError(f"Parsed JSON is not an object: {parsed}")
        return parsed
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON input: {e}")


def parse_xml(input: str) -> dict[str, Any]:
    """Parse an XML string into a Python object."""
    try:
        cleaned_response = input.strip()
        if cleaned_response.startswith("```xml"):
            cleaned_response = cleaned_response[6:]
        if cleaned_response.endswith("```"):
            cleaned_response = cleaned_response[:-3]
        cleaned_response = cleaned_response.strip()

        cleaned_response = cleaned_response.replace("&", "&amp;")
        tree = ET.fromstring(cleaned_response)
        result = {c.tag: c.text for c in tree}

        return result
    except Exception as e:
        raise ValueError(f"Invalid XML input: {e}")


def execute(decoder: Decoder, **kwargs: dict[str, Any]) -> list[Variable]:
    """Execute a decoder step with the provided arguments.

    Args:
        decoder: The decoder step to execute.
        **kwargs: Additional keyword arguments.
    """

    if len(decoder.inputs) != 1:
        raise ValueError(
            f"Decoder step {decoder.id} must have exactly one input, found {len(decoder.inputs)}."
        )

    # get the string value to decode
    input = decoder.inputs[0].value
    if not isinstance(input, str):
        raise ValueError(
            f"Input to decoder step {decoder.id} must be a string, found {type(input).__name__}."
        )

    if decoder.format == DecoderFormat.json:
        result_dict = parse_json(input)
    elif decoder.format == DecoderFormat.xml:
        result_dict = parse_xml(input)
    else:
        raise ValueError(
            f"Unsupported decoder format: {decoder.format}. Supported formats are: {DecoderFormat.json}, {DecoderFormat.xml}."
        )

    # Set the output variables with the parsed results
    for output in decoder.outputs:
        if output.id in result_dict:
            output.value = result_dict[output.id]
        else:
            raise ValueError(
                f"Output variable {output.id} not found in decoded result: {result_dict}"
            )
    return decoder.outputs
