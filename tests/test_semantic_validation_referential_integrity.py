"""
Unit tests for QType semantic validation - Section 2: Referential Integrity.

This module tests that all component references point to existing components
as defined in semantic_ir.md Section 2.
"""

import unittest

from qtype.dsl.model import (
    AuthorizationProvider,
    EmbeddingModel,
    Flow,
    FlowMode,
    Variable,
    Memory,
    MemoryType,
    Prompt,
    QTypeSpec,
    Step,
    TelemetrySink,ToolProvider,
    VariableType,
    VectorDBRetriever,
)
from qtype.ir.validator import SemanticValidationError, validate_semantics


class ReferentialIntegrityTest(unittest.TestCase):
    """Test Section 2: Referential Integrity validation rules."""

    def test_prompt_inputs_valid_reference_success(self) -> None:
        """Test that prompt inputs referencing existing Variable.id passes."""
        spec = QTypeSpec(
            version="1.0",
            inputs=[
                Variable(id="user_name", type=VariableType.text),
                Variable(id="user_age", type=VariableType.number),
            ],
            prompts=[
                Prompt(
                    id="greeting",
                    template="Hello {user_name}, you are {user_age} years old",
                    inputs=["user_name", "user_age"],
                )
            ],
        )
        validate_semantics(spec)

    def test_prompt_inputs_invalid_reference_failure(self) -> None:
        """Test that prompt inputs referencing non-existent Variable.id fails."""
        spec = QTypeSpec(
            version="1.0",
            inputs=[Variable(id="user_name", type=VariableType.text)],
            prompts=[
                Prompt(
                    id="greeting",
                    template="Hello {user_name}, you are {nonexistent} years old",
                    inputs=["user_name", "nonexistent"],
                )
            ],
        )
        with self.assertRaises(SemanticValidationError) as context:
            validate_semantics(spec)
        self.assertIn(
            "Prompt 'greeting' references non-existent input variable 'nonexistent'",
            str(context.exception),
        )

    def test_prompt_outputs_valid_reference_success(self) -> None:
        """Test that prompt outputs referencing existing Output.id passes."""
        spec = QTypeSpec(
            version="1.0",
            inputs=[Variable(id="user_input", type=VariableType.text)],
            prompts=[
                Prompt(
                    id="generator",
                    template="Generate: {user_input}",
                    inputs=["user_input"],
                    outputs=["generated_output"],
                )
            ],
        )
        validate_semantics(spec)

    def test_step_component_valid_prompt_reference_success(self) -> None:
        """Test that step component referencing existing Prompt.id passes."""
        spec = QTypeSpec(
            version="1.0",
            inputs=[Variable(id="user_input", type=VariableType.text)],
            prompts=[
                Prompt(
                    id="test_prompt",
                    template="Process: {user_input}",
                    inputs=["user_input"],
                    outputs=["result"],
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
                            inputs=["user_input"],
                            outputs=["result"],
                        )
                    ],
                )
            ],
        )
        validate_semantics(spec)

    def test_step_component_invalid_reference_failure(self) -> None:
        """Test that step component referencing non-existent component fails."""
        spec = QTypeSpec(
            version="1.0",
            inputs=[Variable(id="user_input", type=VariableType.text)],
            flows=[
                Flow(
                    id="test_flow",
                    mode=FlowMode.complete,
                    steps=[
                        Step(
                            id="step1",
                            component="nonexistent_prompt",
                            inputs=["user_input"],
                            outputs=["result"],
                        )
                    ],
                )
            ],
        )
        with self.assertRaises(SemanticValidationError) as context:
            validate_semantics(spec)
        self.assertIn(
            "Step 'step1' references non-existent component 'nonexistent_prompt'",
            str(context.exception),
        )

    def test_step_inputs_valid_reference_success(self) -> None:
        """Test that step inputs referencing existing Variable.id passes."""
        spec = QTypeSpec(
            version="1.0",
            inputs=[Variable(id="user_input", type=VariableType.text)],
            prompts=[
                Prompt(
                    id="test_prompt",
                    template="Process: {user_input}",
                    inputs=["user_input"],
                    outputs=["result"],
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
                            inputs=["user_input"],
                            outputs=["result"],
                        )
                    ],
                )
            ],
        )
        validate_semantics(spec)

    def test_step_inputs_invalid_reference_failure(self) -> None:
        """Test that step inputs referencing non-existent Variable.id fails."""
        spec = QTypeSpec(
            version="1.0",
            inputs=[Variable(id="user_input", type=VariableType.text)],
            prompts=[
                Prompt(
                    id="test_prompt",
                    template="Process: {user_input}",
                    inputs=["user_input"],
                    outputs=["result"],
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
                            inputs=["nonexistent_input"],
                            outputs=["result"],
                        )
                    ],
                )
            ],
        )
        with self.assertRaises(SemanticValidationError) as context:
            validate_semantics(spec)
        self.assertIn(
            "Step 'step1' references non-existent input variable 'nonexistent_input'",
            str(context.exception),
        )

    def test_retriever_embedding_model_valid_reference_success(self) -> None:
        """Test that retriever embedding_model referencing existing EmbeddingModel.id passes."""
        spec = QTypeSpec(
            version="1.0",
            models=[
                EmbeddingModel(
                    id="embed_model", provider="openai", dimensions=1536
                )
            ],
            retrievers=[
                VectorDBRetriever(
                    id="vector_retriever",
                    index="test_index",
                    embedding_model="embed_model",
                )
            ],
        )
        validate_semantics(spec)

    def test_retriever_embedding_model_invalid_reference_failure(self) -> None:
        """Test that retriever embedding_model referencing non-existent model fails."""
        spec = QTypeSpec(
            version="1.0",
            retrievers=[
                VectorDBRetriever(
                    id="vector_retriever",
                    index="test_index",
                    embedding_model="nonexistent_model",
                )
            ],
        )
        with self.assertRaises(SemanticValidationError) as context:
            validate_semantics(spec)
        self.assertIn(
            "Retriever 'vector_retriever' references non-existent embedding model 'nonexistent_model'",
            str(context.exception),
        )

    def test_memory_embedding_model_valid_reference_success(self) -> None:
        """Test that memory embedding_model referencing existing EmbeddingModel.id passes."""
        spec = QTypeSpec(
            version="1.0",
            models=[
                EmbeddingModel(
                    id="embed_model", provider="openai", dimensions=1536
                )
            ],
            memory=[
                Memory(
                    id="vector_memory",
                    type=MemoryType.vector,
                    embedding_model="embed_model",
                )
            ],
        )
        validate_semantics(spec)

    def test_memory_embedding_model_invalid_reference_failure(self) -> None:
        """Test that memory embedding_model referencing non-existent model fails."""
        spec = QTypeSpec(
            version="1.0",
            memory=[
                Memory(
                    id="vector_memory",
                    type=MemoryType.vector,
                    embedding_model="nonexistent_model",
                )
            ],
        )
        with self.assertRaises(SemanticValidationError) as context:
            validate_semantics(spec)
        self.assertIn(
            "Memory 'vector_memory' references non-existent embedding model 'nonexistent_model'",
            str(context.exception),
        )

    def test_tool_provider_auth_valid_reference_success(self) -> None:
        """Test that tool provider auth referencing existing AuthorizationProvider.id passes."""
        spec = QTypeSpec(
            version="1.0",
            auth=[AuthorizationProvider(id="api_auth", type="api_key")],
            tools=[
                ToolProvider(
                    id="secure_provider",
                    name="Secure Provider",
                    tools=[],
                    auth="api_auth",
                )
            ],
        )
        validate_semantics(spec)

    def test_tool_provider_auth_invalid_reference_failure(self) -> None:
        """Test that tool provider auth referencing non-existent auth provider fails."""
        spec = QTypeSpec(
            version="1.0",
            tools=[
                ToolProvider(
                    id="secure_provider",
                    name="Secure Provider",
                    tools=[],
                    auth="nonexistent_auth",
                )
            ],
        )
        with self.assertRaises(SemanticValidationError) as context:
            validate_semantics(spec)
        self.assertIn(
            "ToolProvider 'secure_provider' references non-existent auth provider 'nonexistent_auth'",
            str(context.exception),
        )

    def test_flow_inputs_valid_reference_success(self) -> None:
        """Test that flow inputs referencing existing Variable.id passes."""
        spec = QTypeSpec(
            version="1.0",
            inputs=[Variable(id="flow_input", type=VariableType.text)],
            flows=[
                Flow(
                    id="test_flow",
                    mode=FlowMode.complete,
                    inputs=["flow_input"],
                    steps=[],
                )
            ],
        )
        validate_semantics(spec)

    def test_flow_inputs_invalid_reference_failure(self) -> None:
        """Test that flow inputs referencing non-existent Variable.id fails."""
        spec = QTypeSpec(
            version="1.0",
            flows=[
                Flow(
                    id="test_flow",
                    mode=FlowMode.complete,
                    inputs=["nonexistent_input"],
                    steps=[],
                )
            ],
        )
        with self.assertRaises(SemanticValidationError) as context:
            validate_semantics(spec)
        self.assertIn(
            "Flow 'test_flow' references non-existent input variable 'nonexistent_input'",
            str(context.exception),
        )

    def test_flow_memory_valid_reference_success(self) -> None:
        """Test that flow memory referencing existing Memory.id passes."""
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

    def test_flow_memory_invalid_reference_failure(self) -> None:
        """Test that flow memory referencing non-existent Memory.id fails."""
        spec = QTypeSpec(
            version="1.0",
            flows=[
                Flow(
                    id="chat_flow",
                    mode=FlowMode.chat,
                    memory=["nonexistent_memory"],
                    steps=[],
                )
            ],
        )
        with self.assertRaises(SemanticValidationError) as context:
            validate_semantics(spec)
        self.assertIn(
            "Flow 'chat_flow' references non-existent memory 'nonexistent_memory'",
            str(context.exception),
        )

    def test_telemetry_sink_auth_valid_reference_success(self) -> None:
        """Test that telemetry sink auth referencing existing AuthorizationProvider.id passes."""
        spec = QTypeSpec(
            version="1.0",
            auth=[AuthorizationProvider(id="telemetry_auth", type="api_key")],
            telemetry=[
                TelemetrySink(
                    id="secure_sink",
                    endpoint="https://secure-telemetry.example.com/events",
                    auth="telemetry_auth",
                )
            ],
        )
        validate_semantics(spec)

    def test_telemetry_sink_auth_invalid_reference_failure(self) -> None:
        """Test that telemetry sink auth referencing non-existent auth provider fails."""
        spec = QTypeSpec(
            version="1.0",
            telemetry=[
                TelemetrySink(
                    id="broken_sink",
                    endpoint="https://telemetry.example.com/events",
                    auth="nonexistent_auth",
                )
            ],
        )
        with self.assertRaises(SemanticValidationError) as context:
            validate_semantics(spec)
        self.assertIn(
            "TelemetrySink 'broken_sink' references non-existent auth provider 'nonexistent_auth'",
            str(context.exception),
        )


if __name__ == "__main__":
    unittest.main()
