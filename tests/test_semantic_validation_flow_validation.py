"""
Unit tests for QType semantic validation - Section 3: Flow Validation.

This module tests flow validation rules including step uniqueness,
conditional logic, and memory requirements as defined in semantic_ir.md Section 3.
"""

import unittest

from qtype.dsl.model import (
    Condition,
    EmbeddingModel,
    Flow,
    FlowMode,
    Input,
    Memory,
    MemoryType,
    Prompt,
    QTypeSpec,
    Step,
    VariableType,
)
from qtype.ir.validator import SemanticValidationError, validate_semantics


class FlowValidationTest(unittest.TestCase):
    """Test Section 3: Flow Validation rules."""

    def test_unique_step_ids_within_flow_success(self) -> None:
        """Test that unique step IDs within a flow pass validation."""
        spec = QTypeSpec(
            version="1.0",
            inputs=[Input(id="user_input", type=VariableType.text)],
            prompts=[
                Prompt(
                    id="test_prompt",
                    template="Process: {user_input}",
                    input_vars=["user_input"],
                    output_vars=["result"],
                )
            ],
            flows=[
                Flow(
                    id="test_flow",
                    mode=FlowMode.complete,
                    steps=[
                        Step(
                            id="step1",
                            component="test_prompt",
                            input_vars=["user_input"],
                            output_vars=["result1"],
                        ),
                        Step(
                            id="step2",
                            component="test_prompt",
                            input_vars=["user_input"],
                            output_vars=["result2"],
                        ),
                    ],
                )
            ],
        )
        validate_semantics(spec)

    def test_nested_flow_reference_success(self) -> None:
        """Test that valid nested flow references pass validation."""
        spec = QTypeSpec(
            version="1.0",
            flows=[
                Flow(id="nested_flow", mode=FlowMode.complete, steps=[]),
                Flow(
                    id="parent_flow",
                    mode=FlowMode.complete,
                    steps=["nested_flow"],
                ),
            ],
        )
        validate_semantics(spec)

    def test_nested_flow_invalid_reference_failure(self) -> None:
        """Test that invalid nested flow references fail validation."""
        spec = QTypeSpec(
            version="1.0",
            flows=[
                Flow(
                    id="parent_flow",
                    mode=FlowMode.complete,
                    steps=["nonexistent_flow"],
                )
            ],
        )
        with self.assertRaises(SemanticValidationError) as context:
            validate_semantics(spec)
        self.assertIn(
            "Flow 'parent_flow' references non-existent nested flow 'nonexistent_flow'",
            str(context.exception),
        )

    def test_flow_inputs_outputs_valid_reference_success(self) -> None:
        """Test that flow inputs and outputs referencing valid variables pass."""
        spec = QTypeSpec(
            version="1.0",
            inputs=[Input(id="flow_input", type=VariableType.text)],
            prompts=[
                Prompt(
                    id="test_prompt",
                    template="Process: {flow_input}",
                    input_vars=["flow_input"],
                    output_vars=["flow_output"],
                )
            ],
            flows=[
                Flow(
                    id="test_flow",
                    mode=FlowMode.complete,
                    inputs=["flow_input"],
                    outputs=["flow_output"],
                    steps=[
                        Step(
                            id="step1",
                            component="test_prompt",
                            input_vars=["flow_input"],
                            output_vars=["flow_output"],
                        )
                    ],
                )
            ],
        )
        validate_semantics(spec)

    def test_flow_conditions_valid_references_success(self) -> None:
        """Test that flow conditions reference valid step IDs."""
        spec = QTypeSpec(
            version="1.0",
            inputs=[Input(id="user_input", type=VariableType.text)],
            prompts=[
                Prompt(
                    id="test_prompt",
                    template="Process: {user_input}",
                    input_vars=["user_input"],
                    output_vars=["result"],
                )
            ],
            flows=[
                Flow(
                    id="test_flow",
                    mode=FlowMode.complete,
                    steps=[
                        Step(
                            id="step1",
                            component="test_prompt",
                            input_vars=["user_input"],
                            output_vars=["result"],
                        ),
                        Step(
                            id="step2",
                            component="test_prompt",
                            input_vars=["user_input"],
                            output_vars=["result2"],
                        ),
                    ],
                    conditions=[
                        Condition(
                            if_var="result",
                            exists=True,
                            then=["step2"],
                        )
                    ],
                )
            ],
        )
        validate_semantics(spec)

    def test_flow_conditions_invalid_references_failure(self) -> None:
        """Test that flow conditions referencing invalid step IDs fail."""
        spec = QTypeSpec(
            version="1.0",
            inputs=[Input(id="user_input", type=VariableType.text)],
            prompts=[
                Prompt(
                    id="test_prompt",
                    template="Process: {user_input}",
                    input_vars=["user_input"],
                    output_vars=["result"],
                )
            ],
            flows=[
                Flow(
                    id="test_flow",
                    mode=FlowMode.complete,
                    steps=[
                        Step(
                            id="step1",
                            component="test_prompt",
                            input_vars=["user_input"],
                            output_vars=["result"],
                        )
                    ],
                    conditions=[
                        Condition(
                            if_var="result",
                            exists=True,
                            then=["nonexistent_step"],
                        )
                    ],
                )
            ],
        )
        with self.assertRaises(SemanticValidationError) as context:
            validate_semantics(spec)
        self.assertIn(
            "Condition in Flow 'test_flow' references non-existent step 'nonexistent_step'",
            str(context.exception),
        )

    def test_chat_mode_requires_memory_success(self) -> None:
        """Test that chat mode flows with memory pass validation."""
        spec = QTypeSpec(
            version="1.0",
            models=[
                EmbeddingModel(
                    id="embed_model", provider="openai", dimensions=1536
                )
            ],
            memory=[
                Memory(
                    id="chat_memory",
                    type=MemoryType.vector,
                    embedding_model="embed_model",
                )
            ],
            flows=[
                Flow(
                    id="chat_flow",
                    mode=FlowMode.chat,
                    memory=["chat_memory"],
                    steps=[],
                )
            ],
        )
        validate_semantics(spec)

    def test_chat_mode_requires_memory_failure(self) -> None:
        """Test that chat mode flows without memory fail validation."""
        spec = QTypeSpec(
            version="1.0",
            flows=[Flow(id="chat_flow", mode=FlowMode.chat, steps=[])],
        )
        with self.assertRaises(SemanticValidationError) as context:
            validate_semantics(spec)
        self.assertIn(
            "Flow 'chat_flow' with mode 'chat' must define memory",
            str(context.exception),
        )

    def test_non_chat_mode_forbids_memory_success(self) -> None:
        """Test that non-chat mode flows without memory pass validation."""
        spec = QTypeSpec(
            version="1.0",
            flows=[Flow(id="complete_flow", mode=FlowMode.complete, steps=[])],
        )
        validate_semantics(spec)

    def test_non_chat_mode_forbids_memory_failure(self) -> None:
        """Test that non-chat mode flows with memory fail validation."""
        spec = QTypeSpec(
            version="1.0",
            models=[
                EmbeddingModel(
                    id="embed_model", provider="openai", dimensions=1536
                )
            ],
            memory=[
                Memory(
                    id="chat_memory",
                    type=MemoryType.vector,
                    embedding_model="embed_model",
                )
            ],
            flows=[
                Flow(
                    id="complete_flow",
                    mode=FlowMode.complete,
                    memory=["chat_memory"],
                    steps=[],
                )
            ],
        )
        with self.assertRaises(SemanticValidationError) as context:
            validate_semantics(spec)
        self.assertIn(
            "Flow 'complete_flow' with mode 'complete' must not define memory",
            str(context.exception),
        )


if __name__ == "__main__":
    unittest.main()
