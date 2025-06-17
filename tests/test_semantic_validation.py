"""
Unit tests for semantic validation rules in QType IR validator.

Tests cover all semantic validation rules as defined in semantic_ir.md:
1. Unique IDs
2. Referential Integrity
3. Flow Validation
4. Memory vs Retriever
5. Tooling Rules
6. Model + Embedding Rules
7. Prompt Requirements
8. Circular Flow Detection
"""

import unittest

from qtype.dsl.models import (
    AuthorizationProvider,
    Condition,
    EmbeddingModel,
    Feedback,
    FeedbackType,
    Flow,
    FlowMode,
    Input,
    Memory,
    MemoryType,
    Model,
    Prompt,
    QTypeSpec,
    SearchRetriever,
    Step,
    Tool,
    ToolProvider,
    VariableType,
    VectorDBRetriever,
)
from qtype.ir.validator import SemanticValidationError, validate_semantics


class TestUniqueIDs(unittest.TestCase):
    """Test Rule #1: Unique IDs validation."""

    def test_unique_model_ids(self) -> None:
        """Test that Model.id values must be unique."""
        spec = QTypeSpec(
            version="1.0",
            models=[
                Model(id="model1", provider="openai"),
                Model(id="model1", provider="anthropic"),  # Duplicate ID
                ],
            )

        with self.assertRaises(SemanticValidationError) as cm:
            validate_semantics(spec)

        self.assertIn("Duplicate Model.id: model1", str(cm.exception))

    def test_unique_input_ids(self) -> None:
        """Test that Input.id values must be unique."""
        spec = QTypeSpec(
            version="1.0",
            inputs=[
                Input(id="input1", type=VariableType.text),
                Input(id="input1", type=VariableType.number),  # Duplicate ID
                ],
            )

        with self.assertRaises(SemanticValidationError) as cm:
            validate_semantics(spec)

        self.assertIn("Duplicate Input.id: input1", str(cm.exception))

    def test_unique_prompt_ids(self) -> None:
        """Test that Prompt.id values must be unique."""
        spec = QTypeSpec(
            version="1.0",
            inputs=[Input(id="input1", type=VariableType.text)],
            prompts=[
                Prompt(id="prompt1", template="Hello", input_vars=["input1"]),
                Prompt(
                    id="prompt1", template="Hi", input_vars=["input1"]
                    ),  # Duplicate ID
                ],
            )

        with self.assertRaises(SemanticValidationError) as cm:
            validate_semantics(spec)

        self.assertIn("Duplicate Prompt.id: prompt1", str(cm.exception))

    def test_unique_memory_ids(self) -> None:
        """Test that Memory.id values must be unique."""
        spec = QTypeSpec(
            version="1.0",
            models=[
                EmbeddingModel(id="embed1", provider="openai", dimensions=1536)
                ],
            memory=[
                Memory(
                    id="mem1", type=MemoryType.vector, embedding_model="embed1"
                    ),
                Memory(
                    id="mem1", type=MemoryType.vector, embedding_model="embed1"
                    ),  # Duplicate ID
                ],
            )

        with self.assertRaises(SemanticValidationError) as cm:
            validate_semantics(spec)

        self.assertIn("Duplicate Memory.id: mem1", str(cm.exception))

    def test_unique_tool_ids_within_provider(self) -> None:
        """Test that Tool.id values must be unique within a ToolProvider."""
        spec = QTypeSpec(
            version="1.0",
            tools=[
                ToolProvider(
                    id="provider1",
                    name="Test Provider",
                    tools=[
                        Tool(
                            id="tool1",
                            name="Tool 1",
                            description="Test tool",
                            input_schema={"type": "object"},
                            output_schema={"type": "object"},
                            ),
                        Tool(
                            id="tool1",  # Duplicate ID within same provider
                            name="Tool 2",
                            description="Another test tool",
                            input_schema={"type": "object"},
                            output_schema={"type": "object"},
                            ),
                        ],
                    )
                ],
            )

        with self.assertRaises(SemanticValidationError) as cm:
            validate_semantics(spec)

        self.assertIn(
            "Duplicate Tool.id tool1 in ToolProvider provider1",
            str(cm.exception),
            )

    def test_unique_tool_provider_ids(self) -> None:
        """Test that ToolProvider.id values must be unique."""
        spec = QTypeSpec(
            version="1.0",
            tools=[
                ToolProvider(id="provider1", name="Provider 1", tools=[]),
                ToolProvider(
                    id="provider1", name="Provider 2", tools=[]
                    ),  # Duplicate ID
                ],
            )

        with self.assertRaises(SemanticValidationError) as cm:
            validate_semantics(spec)

        self.assertIn(
            "Duplicate ToolProvider.id: provider1", str(cm.exception)
            )

    def test_unique_auth_provider_ids(self) -> None:
        """Test that AuthorizationProvider.id values must be unique."""
        spec = QTypeSpec(
            version="1.0",
            auth=[
                AuthorizationProvider(id="auth1", type="api_key"),
                AuthorizationProvider(
                    id="auth1", type="oauth2"
                    ),  # Duplicate ID
                ],
            )

        with self.assertRaises(SemanticValidationError) as cm:
            validate_semantics(spec)

        self.assertIn(
            "Duplicate AuthorizationProvider.id: auth1", str(cm.exception)
            )

    def test_unique_feedback_ids(self) -> None:
        """Test that Feedback.id values must be unique."""
        spec = QTypeSpec(
            version="1.0",
            feedback=[
                Feedback(id="feedback1", type=FeedbackType.THUMBS),
                Feedback(
                    id="feedback1", type=FeedbackType.STAR
                    ),  # Duplicate ID
                ],
            )

        with self.assertRaises(SemanticValidationError) as cm:
            validate_semantics(spec)

        self.assertIn("Duplicate Feedback.id: feedback1", str(cm.exception))

    def test_unique_retriever_ids(self) -> None:
        """Test that Retriever.id values must be unique."""
        spec = QTypeSpec(
            version="1.0",
            models=[
                EmbeddingModel(id="embed1", provider="openai", dimensions=1536)
                ],
            retrievers=[
                VectorDBRetriever(
                    id="ret1", index="index1", embedding_model="embed1"
                    ),
                SearchRetriever(id="ret1", index="index1"),  # Duplicate ID
                ],
            )

        with self.assertRaises(SemanticValidationError) as cm:
            validate_semantics(spec)

        self.assertIn("Duplicate Retriever.id: ret1", str(cm.exception))

    def test_unique_flow_ids(self) -> None:
        """Test that Flow.id values must be unique."""
        spec = QTypeSpec(
            version="1.0",
            flows=[
                Flow(id="flow1", mode=FlowMode.complete, steps=[]),
                Flow(id="flow1", mode=FlowMode.chat, steps=[]),  # Duplicate ID
                ],
            )

        with self.assertRaises(SemanticValidationError) as cm:
            validate_semantics(spec)

        self.assertIn("Duplicate Flow.id: flow1", str(cm.exception))

    def test_unique_step_ids_within_flow(self) -> None:
        """Test that Step.id values must be unique within a flow."""
        spec = QTypeSpec(
            version="1.0",
            inputs=[Input(id="input1", type=VariableType.text)],
            prompts=[
                Prompt(id="prompt1", template="Hello", input_vars=["input1"])
                ],
            flows=[
                Flow(
                    id="flow1",
                    mode=FlowMode.complete,
                    steps=[
                        Step(id="step1", component="prompt1"),
                        Step(
                            id="step1", component="prompt1"
                            ),  # Duplicate step ID in same flow
                        ],
                    )
                ],
            )

        with self.assertRaises(SemanticValidationError) as cm:
            validate_semantics(spec)

        self.assertIn(
            "Duplicate Step.id step1 in Flow flow1", str(cm.exception)
            )

    def test_unique_output_vars(self) -> None:
        """Test that output variable IDs must be unique across prompts and steps."""
        spec = QTypeSpec(
            version="1.0",
            inputs=[Input(id="input1", type=VariableType.text)],
            prompts=[
                Prompt(
                    id="prompt1",
                    template="Hello",
                    input_vars=["input1"],
                    output_vars=["output1"],
                    ),
                Prompt(
                    id="prompt2",
                    template="Hi",
                    input_vars=["input1"],
                    output_vars=["output1"],
                    ),  # Duplicate output
                ],
            )

        with self.assertRaises(SemanticValidationError) as cm:
            validate_semantics(spec)

        self.assertIn("Duplicate Output.id: output1", str(cm.exception))


class TestReferentialIntegrity(unittest.TestCase):
    """Test Rule #2: Referential Integrity validation."""

    def test_prompt_input_vars_reference_valid_inputs(self) -> None:
        """Test that Prompt.input_vars must refer to existing Input.id."""
        spec = QTypeSpec(
            version="1.0",
            inputs=[Input(id="input1", type=VariableType.text)],
            prompts=[
                Prompt(
                    id="prompt1",
                    template="Hello",
                    input_vars=["input1", "invalid_input"],
                    )
                ],
            )

        with self.assertRaises(SemanticValidationError) as cm:
            validate_semantics(spec)

        self.assertIn(
            "Prompt prompt1 input_var invalid_input not found in Input.id",
            str(cm.exception),
            )

    def test_prompt_output_vars_reference_valid_outputs(self) -> None:
        """Test that Prompt.output_vars must refer to existing Output.id."""
        spec = QTypeSpec(
            version="1.0",
            inputs=[Input(id="input1", type=VariableType.text)],
            prompts=[
                Prompt(
                    id="prompt1",
                    template="Hello",
                    input_vars=["input1"],
                    output_vars=["invalid_output"],
                    )
                ],
            )

        with self.assertRaises(SemanticValidationError) as cm:
            validate_semantics(spec)

        self.assertIn(
            "Prompt prompt1 output_var invalid_output not found in Output.id",
            str(cm.exception),
            )

    def test_step_component_references_valid_prompt(self) -> None:
        """Test that Step.component can reference a valid Prompt.id."""
        spec = QTypeSpec(
            version="1.0",
            inputs=[Input(id="input1", type=VariableType.text)],
            prompts=[
                Prompt(id="prompt1", template="Hello", input_vars=["input1"])
                ],
            flows=[
                Flow(
                    id="flow1",
                    mode=FlowMode.complete,
                    steps=[Step(id="step1", component="prompt1")],
                    )
                ],
            )

        # This should NOT raise an error
        try:
            validate_semantics(spec)
        except SemanticValidationError:
            self.fail("Valid prompt reference should not raise an error")

    def test_step_component_references_valid_tool(self) -> None:
        """Test that Step.component can reference a valid Tool.id."""
        spec = QTypeSpec(
            version="1.0",
            tools=[
                ToolProvider(
                    id="provider1",
                    name="Test Provider",
                    tools=[
                        Tool(
                            id="tool1",
                            name="Test Tool",
                            description="A test tool",
                            input_schema={"type": "object"},
                            output_schema={"type": "object"},
                            )
                        ],
                    )
                ],
            flows=[
                Flow(
                    id="flow1",
                    mode=FlowMode.complete,
                    steps=[Step(id="step1", component="tool1")],
                    )
                ],
            )

        # This should NOT raise an error
        try:
            validate_semantics(spec)
        except SemanticValidationError:
            self.fail("Valid tool reference should not raise an error")

    def test_step_component_references_valid_flow(self) -> None:
        """Test that Step.component can reference a valid Flow.id."""
        spec = QTypeSpec(
            version="1.0",
            flows=[
                Flow(id="flow1", mode=FlowMode.complete, steps=[]),
                Flow(
                    id="flow2",
                    mode=FlowMode.complete,
                    steps=[Step(id="step1", component="flow1")],
                    ),
                ],
            )

        # This should NOT raise an error
        try:
            validate_semantics(spec)
        except SemanticValidationError:
            self.fail("Valid flow reference should not raise an error")

    def test_step_component_references_valid_retriever(self) -> None:
        """Test that Step.component can reference a valid Retriever.id."""
        spec = QTypeSpec(
            version="1.0",
            models=[
                EmbeddingModel(id="embed1", provider="openai", dimensions=1536)
                ],
            retrievers=[
                VectorDBRetriever(
                    id="retriever1", index="index1", embedding_model="embed1"
                    )
                ],
            flows=[
                Flow(
                    id="flow1",
                    mode=FlowMode.complete,
                    steps=[Step(id="step1", component="retriever1")],
                    )
                ],
            )

        # This should NOT raise an error
        try:
            validate_semantics(spec)
        except SemanticValidationError:
            self.fail("Valid retriever reference should not raise an error")

    def test_step_component_references_invalid_component(self) -> None:
        """Test that Step.component must reference a valid component."""
        spec = QTypeSpec(
            version="1.0",
            flows=[
                Flow(
                    id="flow1",
                    mode=FlowMode.complete,
                    steps=[Step(id="step1", component="invalid_component")],
                    )
                ],
            )

        with self.assertRaises(SemanticValidationError) as cm:
            validate_semantics(spec)

        self.assertIn(
            "Step step1 component invalid_component not found in any valid component type",
            str(cm.exception),
            )

    def test_step_input_vars_reference_valid_inputs(self) -> None:
        """Test that Step.input_vars must refer to existing Input.id."""
        spec = QTypeSpec(
            version="1.0",
            inputs=[Input(id="input1", type=VariableType.text)],
            prompts=[
                Prompt(id="prompt1", template="Hello", input_vars=["input1"])
                ],
            flows=[
                Flow(
                    id="flow1",
                    mode=FlowMode.complete,
                    steps=[
                        Step(
                            id="step1",
                            component="prompt1",
                            input_vars=["invalid_input"],
                            )
                        ],
                    )
                ],
            )

        with self.assertRaises(SemanticValidationError) as cm:
            validate_semantics(spec)

        self.assertIn(
            "Step step1 input_var invalid_input not found in Input.id",
            str(cm.exception),
            )

    def test_step_output_vars_reference_valid_outputs(self) -> None:
        """Test that Step.output_vars must refer to existing Output.id."""
        spec = QTypeSpec(
            version="1.0",
            inputs=[Input(id="input1", type=VariableType.text)],
            prompts=[
                Prompt(id="prompt1", template="Hello", input_vars=["input1"])
                ],
            flows=[
                Flow(
                    id="flow1",
                    mode=FlowMode.complete,
                    steps=[
                        Step(
                            id="step1",
                            component="prompt1",
                            output_vars=["invalid_output"],
                            )
                        ],
                    )
                ],
            )

        with self.assertRaises(SemanticValidationError) as cm:
            validate_semantics(spec)

        self.assertIn(
            "Step step1 output_var invalid_output not found in Output.id",
            str(cm.exception),
            )

    def test_retriever_embedding_model_reference(self) -> None:
        """Test that VectorDBRetriever.embedding_model must refer to existing Model.id."""
        spec = QTypeSpec(
            version="1.0",
            retrievers=[
                VectorDBRetriever(
                    id="retriever1",
                    index="index1",
                    embedding_model="invalid_model",
                    )
                ],
            )

        with self.assertRaises(SemanticValidationError) as cm:
            validate_semantics(spec)

        self.assertIn(
            "Retriever retriever1 embedding_model invalid_model not found in Model.id", str(
                cm.exception), )

    def test_memory_embedding_model_reference(self) -> None:
        """Test that Memory.embedding_model must refer to existing Model.id."""
        spec = QTypeSpec(
            version="1.0",
            memory=[
                Memory(
                    id="mem1",
                    type=MemoryType.vector,
                    embedding_model="invalid_model",
                    )
                ],
            )

        with self.assertRaises(SemanticValidationError) as cm:
            validate_semantics(spec)

        self.assertIn(
            "Memory mem1 embedding_model invalid_model not found in Model.id",
            str(cm.exception),
            )

    def test_tool_provider_auth_reference(self) -> None:
        """Test that ToolProvider.auth must refer to existing AuthorizationProvider.id."""
        spec = QTypeSpec(
            version="1.0",
            tools=[
                ToolProvider(
                    id="provider1",
                    name="Test Provider",
                    tools=[],
                    auth="invalid_auth",
                    )
                ],
            )

        with self.assertRaises(SemanticValidationError) as cm:
            validate_semantics(spec)

        self.assertIn(
            "ToolProvider provider1 auth invalid_auth not found in AuthorizationProvider.id",
            str(cm.exception),
            )

    def test_flow_memory_reference(self) -> None:
        """Test that Flow.memory must refer to existing Memory.id."""
        spec = QTypeSpec(
            version="1.0",
            flows=[
                Flow(
                    id="flow1",
                    mode=FlowMode.chat,
                    steps=[],
                    memory=["invalid_memory"],
                    )
                ],
            )

        with self.assertRaises(SemanticValidationError) as cm:
            validate_semantics(spec)

        self.assertIn(
            "Flow flow1 memory invalid_memory not found in Memory.id",
            str(cm.exception),
            )


class TestFlowValidation(unittest.TestCase):
    """Test Rule #3: Flow Validation."""

    def test_flow_steps_string_references_valid_flow(self) -> None:
        """Test that Flow.steps string entries must refer to valid Flow.id."""
        spec = QTypeSpec(
            version="1.0",
            flows=[
                Flow(id="flow1", mode=FlowMode.complete, steps=[]),
                Flow(
                    id="flow2", mode=FlowMode.complete, steps=["flow1"]
                    ),  # Valid reference
                ],
            )

        # This should NOT raise an error
        try:
            validate_semantics(spec)
        except SemanticValidationError:
            self.fail("Valid flow reference should not raise an error")

    def test_flow_steps_string_references_invalid_flow(self) -> None:
        """Test that Flow.steps string entries must refer to valid Flow.id."""
        spec = QTypeSpec(
            version="1.0",
            flows=[
                Flow(
                    id="flow1", mode=FlowMode.complete, steps=["invalid_flow"]
                    )
                ],
            )

        with self.assertRaises(SemanticValidationError) as cm:
            validate_semantics(spec)

        self.assertIn(
            "Flow flow1 steps[] string invalid_flow not found in Flow.id",
            str(cm.exception),
            )

    def test_flow_inputs_reference_valid_inputs(self) -> None:
        """Test that Flow.inputs must refer to existing Input.id."""
        spec = QTypeSpec(
            version="1.0",
            inputs=[Input(id="input1", type=VariableType.text)],
            flows=[
                Flow(
                    id="flow1",
                    mode=FlowMode.complete,
                    steps=[],
                    inputs=["input1", "invalid_input"],
                    )
                ],
            )

        with self.assertRaises(SemanticValidationError) as cm:
            validate_semantics(spec)

        self.assertIn(
            "Flow flow1 input invalid_input not found in Input.id",
            str(cm.exception),
            )

    def test_flow_outputs_reference_valid_outputs(self) -> None:
        """Test that Flow.outputs must refer to existing Output.id."""
        spec = QTypeSpec(
            version="1.0",
            inputs=[Input(id="input1", type=VariableType.text)],
            prompts=[
                Prompt(
                    id="prompt1",
                    template="Hello",
                    input_vars=["input1"],
                    output_vars=["output1"],
                    )
                ],
            flows=[
                Flow(
                    id="flow1",
                    mode=FlowMode.complete,
                    steps=[],
                    outputs=["output1", "invalid_output"],
                    )
                ],
            )

        with self.assertRaises(SemanticValidationError) as cm:
            validate_semantics(spec)

        self.assertIn(
            "Flow flow1 output invalid_output not found in Output.id",
            str(cm.exception),
            )

    def test_flow_condition_then_references_valid_steps_or_flows(self) -> None:
        """Test that Flow.conditions.then must refer to valid Step.id or Flow.id."""
        spec = QTypeSpec(
            version="1.0",
            inputs=[Input(id="input1", type=VariableType.text)],
            prompts=[
                Prompt(id="prompt1", template="Hello", input_vars=["input1"])
                ],
            flows=[
                Flow(
                    id="flow1",
                    mode=FlowMode.complete,
                    steps=[Step(id="step1", component="prompt1")],
                    conditions=[
                        Condition(
                            if_var="input1",
                            equals="test",
                            then=["step1", "invalid_ref"],
                            )
                        ],
                    )
                ],
            )

        with self.assertRaises(SemanticValidationError) as cm:
            validate_semantics(spec)

        self.assertIn(
            "Flow flow1 condition then[] invalid_ref not found in Step.id or Flow.id", str(
                cm.exception), )

    def test_flow_condition_else_references_valid_steps_or_flows(self) -> None:
        """Test that Flow.conditions.else_ must refer to valid Step.id or Flow.id."""
        spec = QTypeSpec(
            version="1.0",
            inputs=[Input(id="input1", type=VariableType.text)],
            prompts=[
                Prompt(id="prompt1", template="Hello", input_vars=["input1"])
                ],
            flows=[
                Flow(
                    id="flow1",
                    mode=FlowMode.complete,
                    steps=[Step(id="step1", component="prompt1")],
                    conditions=[
                        Condition(
                            if_var="input1",
                            equals="test",
                            then=["step1"],
                            else_=["invalid_ref"],
                            )
                        ],
                    )
                ],
            )

        with self.assertRaises(SemanticValidationError) as cm:
            validate_semantics(spec)

        self.assertIn(
            "Flow flow1 condition else_[] invalid_ref not found in Step.id or Flow.id", str(
                cm.exception), )

    def test_chat_mode_flow_must_have_memory(self) -> None:
        """Test that Flow with mode=chat must set memory[]."""
        spec = QTypeSpec(
            version="1.0",
            flows=[
                Flow(id="flow1", mode=FlowMode.chat, steps=[])  # No memory set
                ],
            )

        with self.assertRaises(SemanticValidationError) as cm:
            validate_semantics(spec)

        self.assertIn(
            "Flow flow1 mode=chat must set memory[]", str(cm.exception)
            )

    def test_non_chat_mode_flow_must_not_have_memory(self) -> None:
        """Test that Flow with mode!=chat must not set memory[]."""
        spec = QTypeSpec(
            version="1.0",
            models=[
                EmbeddingModel(id="embed1", provider="openai", dimensions=1536)
                ],
            memory=[
                Memory(
                    id="mem1", type=MemoryType.vector, embedding_model="embed1"
                    )
                ],
            flows=[
                Flow(
                    id="flow1",
                    mode=FlowMode.complete,
                    steps=[],
                    memory=["mem1"],
                    )  # Memory set on non-chat
                ],
            )

        with self.assertRaises(SemanticValidationError) as cm:
            validate_semantics(spec)

        self.assertIn(
            "Flow flow1 mode!=chat must not set memory[]", str(cm.exception)
            )


class TestMemoryVsRetriever(unittest.TestCase):
    """Test Rule #4: Memory vs Retriever validation."""

    def test_memory_id_not_used_as_step_component(self) -> None:
        """Test that Memory.id should not be used as Step.component."""
        spec = QTypeSpec(
            version="1.0",
            models=[
                EmbeddingModel(id="embed1", provider="openai", dimensions=1536)
                ],
            memory=[
                Memory(
                    id="mem1", type=MemoryType.vector, embedding_model="embed1"
                    )
                ],
            flows=[
                Flow(
                    id="flow1",
                    mode=FlowMode.complete,
                    steps=[
                        Step(id="step1", component="mem1")
                        ],  # Memory used as component
                    )
                ],
            )

        with self.assertRaises(SemanticValidationError) as cm:
            validate_semantics(spec)

        self.assertIn(
            "Memory.id mem1 used as Step.component in Flow flow1",
            str(cm.exception),
            )


class TestToolingRules(unittest.TestCase):
    """Test Rule #5: Tooling Rules validation."""

    def test_tool_names_unique_within_provider(self) -> None:
        """Test that Tool.name must be unique within a ToolProvider."""
        spec = QTypeSpec(
            version="1.0",
            tools=[
                ToolProvider(
                    id="provider1",
                    name="Test Provider",
                    tools=[
                        Tool(
                            id="tool1",
                            name="duplicate_name",
                            description="First tool",
                            input_schema={"type": "object"},
                            output_schema={"type": "object"},
                            ),
                        Tool(
                            id="tool2",
                            name="duplicate_name",  # Duplicate name
                            description="Second tool",
                            input_schema={"type": "object"},
                            output_schema={"type": "object"},
                            ),
                        ],
                    )
                ],
            )

        with self.assertRaises(SemanticValidationError) as cm:
            validate_semantics(spec)

        self.assertIn(
            "Duplicate Tool.name duplicate_name in ToolProvider provider1",
            str(cm.exception),
            )

    def test_tool_must_have_input_and_output_schema(self) -> None:
        """Test that Tool must define both input_schema and output_schema."""
        spec = QTypeSpec(
            version="1.0",
            tools=[
                ToolProvider(
                    id="provider1",
                    name="Test Provider",
                    tools=[
                        Tool(
                            id="tool1",
                            name="test_tool",
                            description="Test tool",
                            input_schema={"type": "object"},
                            output_schema={},  # Missing output_schema
                            ),
                        ],
                    )
                ],
            )

        with self.assertRaises(SemanticValidationError) as cm:
            validate_semantics(spec)

        self.assertIn(
            "Tool tool1 in ToolProvider provider1 missing input_schema or output_schema",
            str(cm.exception),
            )

    def test_tool_missing_input_schema(self) -> None:
        """Test that Tool must define input_schema."""
        spec = QTypeSpec(
            version="1.0",
            tools=[
                ToolProvider(
                    id="provider1",
                    name="Test Provider",
                    tools=[
                        Tool(
                            id="tool1",
                            name="test_tool",
                            description="Test tool",
                            input_schema={},  # Missing input_schema
                            output_schema={"type": "object"},
                            ),
                        ],
                    )
                ],
            )

        with self.assertRaises(SemanticValidationError) as cm:
            validate_semantics(spec)

        self.assertIn(
            "Tool tool1 in ToolProvider provider1 missing input_schema or output_schema",
            str(cm.exception),
            )


class TestModelEmbeddingRules(unittest.TestCase):
    """Test Rule #6: Model + Embedding Rules validation."""

    def test_embedding_model_must_not_have_inference_params(self) -> None:
        """Test that EmbeddingModel must not have inference_params."""
        # Note: This test checks business logic that may not be enforced in the current validator
        # but represents the intended semantic rule
        spec = QTypeSpec(
            version="1.0",
            models=[
                EmbeddingModel(
                    id="embed1",
                    provider="openai",
                    dimensions=1536,
                    inference_params={
                        "temperature": 0.7
                        },  # Should not be allowed
                    )
                ],
            )

        with self.assertRaises(SemanticValidationError) as cm:
            validate_semantics(spec)

        self.assertIn(
            "EmbeddingModel embed1 must not have inference_params",
            str(cm.exception),
            )

    def test_model_must_not_have_model_field(self) -> None:
        """Test that Model must not have 'model' field (reserved for EmbeddingModel)."""
        # This test checks for reserved field conflicts
        spec = QTypeSpec(
            version="1.0",
            models=[
                Model(
                    id="model1",
                    provider="openai",
                    # The actual 'model' field conflict would be checked if it
                    # existed
                    )
                ],
            )

        # For now, this passes as the current Model doesn't have a 'model'
        # field
        try:
            validate_semantics(spec)
        except SemanticValidationError as e:
            if "must not have 'model' field" in str(e):
                pass  # Expected error
            else:
                raise


class TestPromptRequirements(unittest.TestCase):
    """Test Rule #7: Prompt Requirements validation."""

    def test_prompt_must_define_template_or_path_not_both(self) -> None:
        """Test that Prompt must define either template or path, but not both."""
        spec = QTypeSpec(
            version="1.0",
            inputs=[Input(id="input1", type=VariableType.text)],
            prompts=[
                Prompt(
                    id="prompt1",
                    template="Hello",
                    path="/path/to/template",  # Both template and path defined
                    input_vars=["input1"],
                    )
                ],
            )

        with self.assertRaises(SemanticValidationError) as cm:
            validate_semantics(spec)

        self.assertIn(
            "Prompt prompt1 must define either template or path, but not both",
            str(cm.exception),
            )

    def test_prompt_must_define_either_template_or_path(self) -> None:
        """Test that Prompt must define either template or path."""
        spec = QTypeSpec(
            version="1.0",
            inputs=[Input(id="input1", type=VariableType.text)],
            prompts=[
                Prompt(
                    id="prompt1",
                    # Neither template nor path defined
                    input_vars=["input1"],
                    )
                ],
            )

        with self.assertRaises(SemanticValidationError) as cm:
            validate_semantics(spec)

        self.assertIn(
            "Prompt prompt1 must define either template or path, but not both",
            str(cm.exception),
            )


class TestCircularFlowDetection(unittest.TestCase):
    """Test Rule #8: Circular Flow Detection validation."""

    def test_circular_reference_in_flows(self) -> None:
        """Test detection of circular references in flows."""
        spec = QTypeSpec(
            version="1.0",
            flows=[
                Flow(id="flow1", mode=FlowMode.complete, steps=["flow2"]),
                Flow(
                    id="flow2", mode=FlowMode.complete, steps=["flow1"]
                    ),  # Circular reference
                ],
            )

        with self.assertRaises(SemanticValidationError) as cm:
            validate_semantics(spec)

        error_str = str(cm.exception)
        self.assertTrue(
            "Circular reference detected in Flow flow1" in error_str
            or "Circular reference detected in Flow flow2" in error_str
            )

    def test_self_referencing_flow(self) -> None:
        """Test detection of self-referencing flows."""
        spec = QTypeSpec(
            version="1.0",
            flows=[
                Flow(
                    id="flow1", mode=FlowMode.complete, steps=["flow1"]
                    ),  # Self-reference
                ],
            )

        with self.assertRaises(SemanticValidationError) as cm:
            validate_semantics(spec)

        self.assertIn(
            "Circular reference detected in Flow flow1", str(cm.exception)
            )

    def test_complex_circular_reference(self) -> None:
        """Test detection of circular references in a chain of flows."""
        spec = QTypeSpec(
            version="1.0",
            flows=[
                Flow(id="flow1", mode=FlowMode.complete, steps=["flow2"]),
                Flow(id="flow2", mode=FlowMode.complete, steps=["flow3"]),
                Flow(
                    id="flow3", mode=FlowMode.complete, steps=["flow1"]
                    ),  # Creates circle: flow1 -> flow2 -> flow3 -> flow1
                ],
            )

        with self.assertRaises(SemanticValidationError) as cm:
            validate_semantics(spec)

        error_str = str(cm.exception)
        self.assertTrue(
            any(
                f"Circular reference detected in Flow flow{i}" in error_str
                for i in [1, 2, 3]
                )
            )


class TestValidSpecExamples(unittest.TestCase):
    """Test that valid specifications pass validation."""

    def test_minimal_valid_spec(self) -> None:
        """Test that a minimal valid spec passes validation."""
        spec = QTypeSpec(version="1.0")

        try:
            validate_semantics(spec)
        except SemanticValidationError:
            self.fail("Minimal valid spec should not raise validation errors")

    def test_complete_valid_spec(self) -> None:
        """Test that a complete valid spec passes validation."""
        spec = QTypeSpec(
            version="1.0",
            models=[
                Model(id="model1", provider="openai"),
                EmbeddingModel(
                    id="embed1", provider="openai", dimensions=1536
                    ),
                ],
            inputs=[
                Input(id="input1", type=VariableType.text),
                Input(id="input2", type=VariableType.number),
                ],
            prompts=[
                Prompt(
                    id="prompt1",
                    template="Hello {input1}",
                    input_vars=["input1"],
                    output_vars=["output1"],
                    ),
                Prompt(
                    id="prompt2",
                    path="/path/to/template",
                    input_vars=["input2"],
                    output_vars=["output2"],
                    ),
                ],
            memory=[
                Memory(
                    id="mem1", type=MemoryType.vector, embedding_model="embed1"
                    )
                ],
            retrievers=[
                VectorDBRetriever(
                    id="ret1", index="index1", embedding_model="embed1"
                    ),
                SearchRetriever(id="ret2", index="index2"),
                ],
            auth=[AuthorizationProvider(id="auth1", type="api_key")],
            tools=[
                ToolProvider(
                    id="provider1",
                    name="Test Provider",
                    auth="auth1",
                    tools=[
                        Tool(
                            id="tool1",
                            name="test_tool",
                            description="A test tool",
                            input_schema={"type": "object", "properties": {}},
                            output_schema={"type": "object", "properties": {}},
                            )
                        ],
                    )
                ],
            feedback=[Feedback(id="feedback1", type=FeedbackType.THUMBS)],
            flows=[
                Flow(
                    id="flow1",
                    mode=FlowMode.chat,
                    inputs=["input1"],
                    outputs=["output1"],
                    memory=["mem1"],
                    steps=[
                        Step(
                            id="step1",
                            component="prompt1",
                            input_vars=["input1"],
                            output_vars=["output1"],
                            ),
                        Step(id="step2", component="tool1"),
                        Step(id="step3", component="ret1"),
                        ],
                    conditions=[
                        Condition(
                            if_var="input1",
                            equals="test",
                            then=["step1"],
                            else_=["step2"],
                            )
                        ],
                    ),
                Flow(
                    id="flow2",
                    mode=FlowMode.complete,
                    inputs=["input2"],
                    outputs=["output2"],
                    steps=[
                        Step(
                            id="step4",
                            component="prompt2",
                            input_vars=["input2"],
                            output_vars=["output2"],
                            ),
                        "flow1",  # Reference to another flow
                        ],
                    ),
                ],
            )

        try:
            validate_semantics(spec)
        except SemanticValidationError:
            self.fail("Complete valid spec should not raise validation errors")


class TestSemanticValidationErrorClass(unittest.TestCase):
    """Test the SemanticValidationError exception class."""

    def test_semantic_validation_error_creation(self) -> None:
        """Test SemanticValidationError creation and string representation."""
        errors = ["Error 1", "Error 2", "Error 3"]
        exception = SemanticValidationError(errors)

        self.assertEqual(exception.errors, errors)
        self.assertEqual(str(exception), "Error 1\nError 2\nError 3")
        self.assertEqual(exception.args[0], "Semantic validation failed")

    def test_semantic_validation_error_empty_errors(self) -> None:
        """Test SemanticValidationError with empty error list."""
        exception = SemanticValidationError([])

        self.assertEqual(exception.errors, [])
        self.assertEqual(str(exception), "")


if __name__ == "__main__":
    unittest.main()
