import json
import xml.etree.ElementTree as ET
from typing import Any, AsyncIterator

from qtype.dsl.model import DecoderFormat
from qtype.interpreter.base.base_step_executor import StepExecutor
from qtype.interpreter.base.executor_context import ExecutorContext
from qtype.interpreter.types import FlowMessage
from qtype.semantic.model import Decoder


class DecoderExecutor(StepExecutor):
    """Executor for Decoder steps."""

    def __init__(
        self, step: Decoder, context: ExecutorContext, **dependencies
    ):
        super().__init__(step, context, **dependencies)
        if not isinstance(step, Decoder):
            raise ValueError("DecoderExecutor can only execute Decoder steps.")
        self.step: Decoder = step

    def _parse_json(self, input_str: str) -> dict[str, Any]:
        """Parse a JSON string into a Python object.

        Args:
            input_str: The JSON string to parse.

        Returns:
            A dictionary parsed from the JSON.

        Raises:
            ValueError: If the JSON is invalid or not an object.
        """
        try:
            cleaned_response = input_str.strip()
            # Remove markdown code fences if present
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
            raise ValueError(f"Invalid JSON input: {e}") from e

    def _parse_xml(self, input_str: str) -> dict[str, Any]:
        """Parse an XML string into a Python object.

        Args:
            input_str: The XML string to parse.

        Returns:
            A dictionary with tag names as keys and text content as values.

        Raises:
            ValueError: If the XML is invalid.
        """
        try:
            cleaned_response = input_str.strip()
            # Remove markdown code fences if present
            if cleaned_response.startswith("```xml"):
                cleaned_response = cleaned_response[6:]
            if cleaned_response.endswith("```"):
                cleaned_response = cleaned_response[:-3]
            cleaned_response = cleaned_response.strip()

            # Escape ampersands
            cleaned_response = cleaned_response.replace("&", "&amp;")
            tree = ET.fromstring(cleaned_response)
            result = {c.tag: c.text for c in tree}

            return result
        except Exception as e:
            raise ValueError(f"Invalid XML input: {e}") from e

    def _parse(self, input_str: str) -> dict[str, Any]:
        """Parse input string based on the decoder format.

        Args:
            input_str: The string to parse.

        Returns:
            A dictionary parsed from the input.

        Raises:
            ValueError: If the format is unsupported or parsing fails.
        """
        if self.step.format == DecoderFormat.json:
            return self._parse_json(input_str)
        elif self.step.format == DecoderFormat.xml:
            return self._parse_xml(input_str)
        else:
            raise ValueError(
                (
                    f"Unsupported decoder format: {self.step.format}. "
                    f"Supported formats are: {DecoderFormat.json}, "
                    f"{DecoderFormat.xml}."
                )
            )

    async def process_message(
        self,
        message: FlowMessage,
    ) -> AsyncIterator[FlowMessage]:
        """Process a single FlowMessage for the Decoder step.

        Args:
            message: The FlowMessage to process.

        Yields:
            A FlowMessage with decoded outputs or an error.
        """
        input_id = self.step.inputs[0].id

        try:
            # Get the input string to decode
            input_value = message.variables.get(input_id)
            if not isinstance(input_value, str):
                raise ValueError(
                    (
                        f"Input to decoder step {self.step.id} must be "
                        f"a string, found {type(input_value).__name__}."
                    )
                )

            await self.stream_emitter.status(
                f"Decoding {self.step.format.value} input"
            )

            # Parse the input
            result_dict = self._parse(input_value)

            # Extract output variables from the parsed result
            output_vars = {}
            for output in self.step.outputs:
                if output.id in result_dict:
                    output_vars[output.id] = result_dict[output.id]
                else:
                    raise ValueError(
                        (
                            f"Output variable {output.id} not found in "
                            f"decoded result: {result_dict}"
                        )
                    )

            await self.stream_emitter.status(
                f"Decoded {len(output_vars)} output variables"
            )

            # Yield the result
            yield message.copy_with_variables(output_vars)

        except Exception as e:
            # Emit error event to stream so frontend can display it
            await self.stream_emitter.error(str(e))
            message.set_error(self.step.id, e)
            yield message
