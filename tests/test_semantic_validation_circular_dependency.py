"""
Unit tests for QType semantic validation - Section 8: Circular Dependencies.

This module tests circular dependency detection in flow references as defined in
semantic_ir.md Section 8.
"""

import unittest

from qtype.dsl.model import (
    Flow,
    FlowMode,
    Variable,
    Prompt,
    QTypeSpec,
    Step,
    VariableTypeEnum,
)
from qtype.ir.validator import SemanticValidationError, validate_semantics


class CircularDependencyTest(unittest.TestCase):
    """Test Section 8: Circular Dependency validation rules."""

    def test_no_circular_references_success(self) -> None:
        """Test that flows without circular references pass validation."""
        spec = QTypeSpec(
            version="1.0",
            flows=[
                Flow(id="flow1", mode=FlowMode.complete, steps=[]),
                Flow(
                    id="flow2",
                    mode=FlowMode.complete,
                    steps=["flow1"],  # flow2 -> flow1 (no cycle)
                ),
                Flow(
                    id="flow3", mode=FlowMode.complete, steps=["flow2"]
                ),  # flow3 -> flow2 -> flow1 (no cycle)
            ],
        )
        validate_semantics(spec)

    def test_direct_circular_reference_failure(self) -> None:
        """Test that direct circular references fail validation."""
        spec = QTypeSpec(
            version="1.0",
            flows=[
                Flow(
                    id="self_referencing",
                    mode=FlowMode.complete,
                    steps=["self_referencing"],  # Direct self-reference
                )
            ],
        )
        with self.assertRaises(SemanticValidationError) as context:
            validate_semantics(spec)
        self.assertIn(
            "Circular reference detected in Flow 'self_referencing'",
            str(context.exception),
        )

    def test_indirect_circular_reference_failure(self) -> None:
        """Test that indirect circular references fail validation."""
        spec = QTypeSpec(
            version="1.0",
            flows=[
                Flow(
                    id="flow1",
                    mode=FlowMode.complete,
                    steps=["flow2"],  # flow1 -> flow2
                ),
                Flow(
                    id="flow2",
                    mode=FlowMode.complete,
                    steps=["flow3"],  # flow2 -> flow3
                ),
                Flow(
                    id="flow3",
                    mode=FlowMode.complete,
                    steps=["flow1"],  # flow3 -> flow1 (creates cycle)
                ),
            ],
        )
        with self.assertRaises(SemanticValidationError) as context:
            validate_semantics(spec)
        # The error should detect the circular reference in at least one of the flows
        error_message = str(context.exception)
        self.assertTrue(
            any(
                f"Circular reference detected in Flow '{flow_id}'"
                in error_message
                for flow_id in ["flow1", "flow2", "flow3"]
            ),
            f"Expected circular reference error, got: {error_message}",
        )

    def test_complex_flow_structure_without_cycles_success(self) -> None:
        """Test complex flow structure without cycles passes validation."""
        spec = QTypeSpec(
            version="1.0",
            inputs=[Variable(id="user_input", type=VariableTypeEnum.text)],
            prompts=[
                Prompt(
                    id="prompt1",
                    template="Process: {user_input}",
                    inputs=["user_input"],
                    outputs=["result1"],
                )
            ],
            flows=[
                Flow(id="base_flow", mode=FlowMode.complete, steps=[]),
                Flow(
                    id="processing_flow",
                    mode=FlowMode.complete,
                    steps=[
                        Step(
                            id="step1",
                            component="prompt1",
                            inputs=["user_input"],
                            outputs=["result1"],
                        ),
                        "base_flow",  # Reference to another flow
                    ],
                ),
                Flow(
                    id="main_flow",
                    mode=FlowMode.complete,
                    steps=[
                        "processing_flow",
                        "base_flow",
                    ],  # Multiple flow references
                ),
            ],
        )
        validate_semantics(spec)

    def test_two_way_circular_reference_failure(self) -> None:
        """Test that two-way circular references fail validation."""
        spec = QTypeSpec(
            version="1.0",
            flows=[
                Flow(
                    id="flowA",
                    mode=FlowMode.complete,
                    steps=["flowB"],  # flowA -> flowB
                ),
                Flow(
                    id="flowB",
                    mode=FlowMode.complete,
                    steps=["flowA"],  # flowB -> flowA (creates cycle)
                ),
            ],
        )
        with self.assertRaises(SemanticValidationError) as context:
            validate_semantics(spec)
        error_message = str(context.exception)
        self.assertTrue(
            any(
                f"Circular reference detected in Flow '{flow_id}'"
                in error_message
                for flow_id in ["flowA", "flowB"]
            ),
            f"Expected circular reference error, got: {error_message}",
        )

    def test_multiple_references_to_same_flow_success(self) -> None:
        """Test that multiple references to the same flow without cycles pass validation."""
        spec = QTypeSpec(
            version="1.0",
            flows=[
                Flow(id="shared_flow", mode=FlowMode.complete, steps=[]),
                Flow(
                    id="flow1",
                    mode=FlowMode.complete,
                    steps=["shared_flow"],
                ),
                Flow(
                    id="flow2",
                    mode=FlowMode.complete,
                    steps=["shared_flow"],
                ),
                Flow(
                    id="main_flow",
                    mode=FlowMode.complete,
                    steps=[
                        "flow1",
                        "flow2",
                        "shared_flow",
                    ],  # Multiple refs to shared_flow
                ),
            ],
        )
        validate_semantics(spec)

    def test_deep_nesting_without_cycles_success(self) -> None:
        """Test that deeply nested flow references without cycles pass validation."""
        spec = QTypeSpec(
            version="1.0",
            flows=[
                Flow(id="level1", mode=FlowMode.complete, steps=[]),
                Flow(id="level2", mode=FlowMode.complete, steps=["level1"]),
                Flow(id="level3", mode=FlowMode.complete, steps=["level2"]),
                Flow(id="level4", mode=FlowMode.complete, steps=["level3"]),
                Flow(id="level5", mode=FlowMode.complete, steps=["level4"]),
            ],
        )
        validate_semantics(spec)

    def test_orphaned_components_are_allowed(self) -> None:
        """Test that orphaned components (defined but not used) are allowed."""
        # Based on the semantic rules, orphaned components should be discouraged
        # but not necessarily cause validation failure. This tests current behavior.
        spec = QTypeSpec(
            version="1.0",
            inputs=[
                Variable(id="used_input", type=VariableTypeEnum.text),
                Variable(
                    id="orphaned_input", type=VariableTypeEnum.text
                ),  # Not used anywhere
            ],
            prompts=[
                Prompt(
                    id="used_prompt",
                    template="Process: {used_input}",
                    inputs=["used_input"],
                    outputs=["result"],
                ),
                Prompt(
                    id="orphaned_prompt",  # Not used anywhere
                    template="Orphaned: {used_input}",
                    inputs=["used_input"],
                    outputs=["orphaned_result"],
                ),
            ],
            flows=[
                Flow(
                    id="main_flow",
                    mode=FlowMode.complete,
                    steps=[
                        Step(
                            id="step1",
                            component="used_prompt",
                            inputs=["used_input"],
                            outputs=["result"],
                        )
                    ],
                )
            ],
        )
        # Should pass validation (orphaned components are allowed)
        validate_semantics(spec)

    def test_complex_circular_dependency_failure(self) -> None:
        """Test that complex circular dependencies with multiple paths fail validation."""
        spec = QTypeSpec(
            version="1.0",
            flows=[
                Flow(
                    id="hub_flow",
                    mode=FlowMode.complete,
                    steps=["spoke1_flow", "spoke2_flow"],
                ),
                Flow(
                    id="spoke1_flow",
                    mode=FlowMode.complete,
                    steps=["shared_flow"],
                ),
                Flow(
                    id="spoke2_flow",
                    mode=FlowMode.complete,
                    steps=["shared_flow"],
                ),
                Flow(
                    id="shared_flow",
                    mode=FlowMode.complete,
                    steps=[
                        "hub_flow"
                    ],  # Creates cycle: hub -> spoke1/spoke2 -> shared -> hub
                ),
            ],
        )
        with self.assertRaises(SemanticValidationError) as context:
            validate_semantics(spec)
        self.assertIn("Circular reference detected", str(context.exception))


if __name__ == "__main__":
    unittest.main()
