from typing import Any, AsyncIterator

from jsonpath_ng.ext import parse  # type: ignore[import-untyped]
from pydantic import BaseModel

from qtype.base.types import PrimitiveTypeEnum
from qtype.dsl.model import ListType
from qtype.interpreter.base.base_step_executor import StepExecutor
from qtype.interpreter.base.executor_context import ExecutorContext
from qtype.interpreter.types import FlowMessage
from qtype.semantic.model import FieldExtractor


class FieldExtractorExecutor(StepExecutor):
    """Executor for FieldExtractor steps.

    Extracts fields from input data using JSONPath expressions and
    constructs output instances. Supports 1-to-many cardinality when
    the JSONPath matches multiple values.
    """

    def __init__(
        self,
        step: FieldExtractor,
        context: ExecutorContext,
        **dependencies: object,
    ):
        super().__init__(step, context, **dependencies)
        if not isinstance(step, FieldExtractor):
            raise ValueError(
                "FieldExtractorExecutor can only execute FieldExtractor steps."
            )
        self.step: FieldExtractor = step

        # Parse the JSONPath expression once at initialization
        try:
            self.jsonpath_expr = parse(self.step.json_path)
        except Exception as e:
            raise ValueError(
                f"Invalid JSONPath expression '{self.step.json_path}': {e}"
            ) from e

    def _to_dict(self, value: Any) -> Any:
        """Convert value to dict representation for JSONPath processing.

        Args:
            value: The value to convert (could be BaseModel, dict, list, etc.)

        Returns:
            Dict representation suitable for JSONPath processing
        """
        if isinstance(value, BaseModel):
            return value.model_dump()
        return value

    def _construct_output(self, extracted_data: Any) -> Any:
        """Construct the output value from extracted data.

        Args:
            extracted_data: The data extracted by JSONPath

        Returns:
            Constructed output value based on the output variable type
        """
        output_var = self.step.outputs[0]
        output_type = output_var.type

        # Handle primitive types - just return the extracted data
        if isinstance(output_type, PrimitiveTypeEnum):
            return extracted_data

        # Handle list types
        if isinstance(output_type, ListType):
            # The extracted_data should already be a list
            if not isinstance(extracted_data, list):
                extracted_data = [extracted_data]
            return extracted_data

        # Handle BaseModel types (domain types and custom types)
        if isinstance(output_type, type) and issubclass(
            output_type, BaseModel
        ):
            # If extracted_data is a dict, use it as kwargs
            if isinstance(extracted_data, dict):
                return output_type(**extracted_data)
            # If it's already the right type, return it
            elif isinstance(extracted_data, output_type):
                return extracted_data
            else:
                raise ValueError(
                    (
                        f"Cannot construct {output_type.__name__} from "
                        f"{type(extracted_data).__name__}"
                    )
                )

        # Fallback - return as-is
        return extracted_data

    async def process_message(
        self,
        message: FlowMessage,
    ) -> AsyncIterator[FlowMessage]:
        """Process a single FlowMessage for the FieldExtractor step.

        Args:
            message: The FlowMessage to process.

        Yields:
            FlowMessage(s) with extracted and constructed output values.
            Multiple messages may be yielded if JSONPath matches multiple values.
        """
        input_id = self.step.inputs[0].id
        output_id = self.step.outputs[0].id

        try:
            # Get the input value
            input_value = message.variables.get(input_id)
            if input_value is None:
                raise ValueError(
                    f"Input variable '{input_id}' is not set or is None"
                )

            await self.stream_emitter.status(
                f"Extracting fields using JSONPath: {self.step.json_path}"
            )

            # Convert input to dict for JSONPath processing
            input_dict = self._to_dict(input_value)

            # Apply JSONPath expression
            matches = self.jsonpath_expr.find(input_dict)

            if not matches:
                raise ValueError(
                    (
                        f"JSONPath expression '{self.step.json_path}' "
                        f"did not match any data in input"
                    )
                )

            await self.stream_emitter.status(
                f"JSONPath matched {len(matches)} value(s)"
            )

            # Yield one message per match (1-to-many)
            for match in matches:
                extracted_data = match.value

                # Construct the output value
                output_value = self._construct_output(extracted_data)

                # Yield message with the constructed output
                yield message.copy_with_variables({output_id: output_value})

        except Exception as e:
            # Emit error event to stream so frontend can display it
            await self.stream_emitter.error(str(e))
            message.set_error(self.step.id, e)
            yield message
