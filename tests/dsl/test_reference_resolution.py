"""
Unit tests for reference resolution in DSL models.

This module tests that string references (e.g., "my_auth_id") are properly
resolved to Reference[T] objects by the normalize_string_references validator
in StrictBaseModel.

Each test loads a YAML spec file that uses string references and verifies
that the loaded model has Reference objects instead of strings.
"""

from __future__ import annotations

from pathlib import Path

from qtype import dsl
from qtype.base.types import Reference
from qtype.dsl import loader, parser

# Path to the reference test specs
REFERENCE_SPECS_DIR = Path(__file__).parent / "reference_specs"


def load_test_spec(spec_filename: str) -> dsl.Application:
    """
    Load a test spec YAML file and parse it into a DSL Application.

    Args:
        spec_filename: Name of the YAML file in the reference_specs directory

    Returns:
        The parsed DSL Application model (before validation/resolution)
    """
    spec_path = REFERENCE_SPECS_DIR / spec_filename

    # Load and parse the YAML file
    yaml_data = loader.load_yaml_file(spec_path)
    root, _ = parser.parse_document(yaml_data)

    if not isinstance(root, dsl.Application):
        raise TypeError(f"Expected Application, got {type(root)}")

    return root


class TestModelReferenceResolution:
    """Test reference resolution for the Model class."""

    def test_model_auth_string_resolved_to_reference(self) -> None:
        """
        Test that Model.auth field containing a string ID is resolved
        to a Reference[AuthProviderType] object.

        The YAML contains:
            auth: test_auth

        After parsing, it should be:
            auth: Reference(ref="test_auth")
        """
        app = load_test_spec("model_auth_reference.qtype.yaml")

        # Get the model from the application
        assert app.models is not None
        assert len(app.models) == 1
        model = app.models[0]

        # Verify the model has the expected ID
        assert model.id == "test_model"

        # The critical assertion: auth should be a Reference object, not a string
        assert model.auth is not None
        assert isinstance(model.auth, Reference), (
            f"Expected model.auth to be a Reference object, "
            f"but got {type(model.auth).__name__}: {model.auth}"
        )

        # Verify the reference points to the correct auth provider
        assert model.auth.ref == "test_auth"


class TestAPIToolReferenceResolution:
    """Test reference resolution for the APITool class."""

    def test_api_tool_auth_string_resolved_to_reference(self) -> None:
        """Test that APITool.auth string is resolved to Reference[AuthProviderType]."""
        app = load_test_spec("api_tool_auth_reference.qtype.yaml")

        assert app.tools is not None
        assert len(app.tools) == 1
        tool = app.tools[0]
        assert isinstance(tool, dsl.APITool)

        assert tool.auth is not None
        assert isinstance(tool.auth, Reference)
        assert tool.auth.ref == "test_api_auth"


class TestStepReferenceResolution:
    """Test reference resolution for Step base class fields (inputs/outputs)."""

    def test_step_inputs_string_resolved_to_reference(self) -> None:
        """Test that Step.inputs list of strings is resolved to list of Reference[Variable]."""
        app = load_test_spec("step_inputs_reference.qtype.yaml")

        assert app.flows is not None
        assert len(app.flows) == 1
        flow = app.flows[0]
        assert len(flow.steps) == 1
        step = flow.steps[0]
        assert isinstance(step, dsl.Step)  # Type narrowing

        assert step.inputs is not None
        assert len(step.inputs) == 1
        assert isinstance(step.inputs[0], Reference)
        assert step.inputs[0].ref == "input_var"

    def test_step_outputs_string_resolved_to_reference(self) -> None:
        """Test that Step.outputs list of strings is resolved to list of Reference[Variable]."""
        app = load_test_spec("step_outputs_reference.qtype.yaml")

        assert app.flows is not None
        assert len(app.flows) == 1
        flow = app.flows[0]
        assert len(flow.steps) == 1
        step = flow.steps[0]
        assert isinstance(step, dsl.Step)  # Type narrowing

        assert step.outputs is not None
        assert len(step.outputs) == 1
        assert isinstance(step.outputs[0], Reference)
        assert step.outputs[0].ref == "output_var"


class TestLLMInferenceReferenceResolution:
    """Test reference resolution for LLMInference class."""

    def test_llm_inference_memory_string_resolved_to_reference(self) -> None:
        """Test that LLMInference.memory string is resolved to Reference[Memory]."""
        app = load_test_spec("llm_inference_memory_reference.qtype.yaml")

        assert app.flows is not None
        flow = app.flows[0]
        step = flow.steps[0]
        assert isinstance(step, dsl.LLMInference)

        assert step.memory is not None
        assert isinstance(step.memory, Reference)
        assert step.memory.ref == "test_memory"

    def test_llm_inference_model_string_resolved_to_reference(self) -> None:
        """Test that LLMInference.model string is resolved to Reference[ModelType]."""
        app = load_test_spec("llm_inference_model_reference.qtype.yaml")

        assert app.flows is not None
        flow = app.flows[0]
        step = flow.steps[0]
        assert isinstance(step, dsl.LLMInference)

        assert isinstance(step.model, Reference)
        assert step.model.ref == "test_model"


class TestAgentReferenceResolution:
    """Test reference resolution for Agent class."""

    def test_agent_tools_string_resolved_to_reference(self) -> None:
        """Test that Agent.tools list of strings is resolved to list of Reference[ToolType]."""
        app = load_test_spec("agent_tools_reference.qtype.yaml")

        assert app.flows is not None
        flow = app.flows[0]
        step = flow.steps[0]
        assert isinstance(step, dsl.Agent)

        assert len(step.tools) == 2
        assert isinstance(step.tools[0], Reference)
        assert step.tools[0].ref == "tool_one"
        assert isinstance(step.tools[1], Reference)
        assert step.tools[1].ref == "tool_two"


class TestFlowInterfaceReferenceResolution:
    """Test reference resolution for FlowInterface class."""

    def test_flow_interface_session_inputs_string_resolved_to_reference(
        self,
    ) -> None:
        """Test that FlowInterface.session_inputs list of strings is resolved to list of Reference[Variable]."""
        app = load_test_spec(
            "flow_interface_session_inputs_reference.qtype.yaml"
        )

        assert app.flows is not None
        flow = app.flows[0]
        assert flow.interface is not None

        assert len(flow.interface.session_inputs) == 1
        assert isinstance(flow.interface.session_inputs[0], Reference)
        assert flow.interface.session_inputs[0].ref == "session_var"


class TestInvokeToolReferenceResolution:
    """Test reference resolution for InvokeTool class."""

    def test_invoke_tool_string_resolved_to_reference(self) -> None:
        """Test that InvokeTool.tool string is resolved to Reference[ToolType]."""
        app = load_test_spec("invoke_tool_reference.qtype.yaml")

        assert app.flows is not None
        flow = app.flows[0]
        step = flow.steps[0]
        assert isinstance(step, dsl.InvokeTool)

        assert isinstance(step.tool, Reference)
        assert step.tool.ref == "test_tool"


class TestInvokeFlowReferenceResolution:
    """Test reference resolution for InvokeFlow class."""

    def test_invoke_flow_string_resolved_to_reference(self) -> None:
        """Test that InvokeFlow.flow string is resolved to Reference[Flow]."""
        app = load_test_spec("invoke_flow_reference.qtype.yaml")

        assert app.flows is not None
        # Second flow contains the InvokeFlow step
        flow = app.flows[1]
        step = flow.steps[0]
        assert isinstance(step, dsl.InvokeFlow)

        assert isinstance(step.flow, Reference)
        assert step.flow.ref == "target_flow"


class TestTelemetrySinkReferenceResolution:
    """Test reference resolution for TelemetrySink class."""

    def test_telemetry_sink_auth_string_resolved_to_reference(self) -> None:
        """Test that TelemetrySink.auth string is resolved to Reference[AuthorizationProvider]."""
        app = load_test_spec("telemetry_sink_auth_reference.qtype.yaml")

        assert app.telemetry is not None
        assert isinstance(app.telemetry, dsl.TelemetrySink)

        assert app.telemetry.auth is not None
        assert isinstance(app.telemetry.auth, Reference)
        assert app.telemetry.auth.ref == "telemetry_auth"


class TestSQLSourceReferenceResolution:
    """Test reference resolution for SQLSource class."""

    def test_sql_source_auth_string_resolved_to_reference(self) -> None:
        """Test that SQLSource.auth string is resolved to Reference[AuthProviderType]."""
        app = load_test_spec("sql_source_auth_reference.qtype.yaml")

        assert app.flows is not None
        flow = app.flows[0]
        step = flow.steps[0]
        assert isinstance(step, dsl.SQLSource)

        assert step.auth is not None
        assert isinstance(step.auth, Reference)
        assert step.auth.ref == "db_auth"


class TestDocumentSourceReferenceResolution:
    """Test reference resolution for DocumentSource class."""

    def test_document_source_auth_string_resolved_to_reference(self) -> None:
        """Test that DocumentSource.auth string is resolved to Reference[AuthProviderType]."""
        app = load_test_spec("document_source_auth_reference.qtype.yaml")

        assert app.flows is not None
        flow = app.flows[0]
        step = flow.steps[0]
        assert isinstance(step, dsl.DocumentSource)

        assert step.auth is not None
        assert isinstance(step.auth, Reference)
        assert step.auth.ref == "doc_auth"


class TestDocumentEmbedderReferenceResolution:
    """Test reference resolution for DocumentEmbedder class."""

    def test_document_embedder_model_string_resolved_to_reference(
        self,
    ) -> None:
        """Test that DocumentEmbedder.model string is resolved to Reference[EmbeddingModel]."""
        app = load_test_spec("document_embedder_model_reference.qtype.yaml")

        assert app.flows is not None
        flow = app.flows[0]
        step = flow.steps[0]
        assert isinstance(step, dsl.DocumentEmbedder)

        assert isinstance(step.model, Reference)
        assert step.model.ref == "embedding_model"


class TestVectorIndexReferenceResolution:
    """Test reference resolution for VectorIndex class."""

    def test_vector_index_auth_string_resolved_to_reference(self) -> None:
        """Test that VectorIndex.auth (Index base class) string is resolved to Reference[AuthProviderType]."""
        app = load_test_spec("vector_index_auth_reference.qtype.yaml")

        assert app.indexes is not None
        assert len(app.indexes) == 1
        index = app.indexes[0]
        assert isinstance(index, dsl.VectorIndex)

        assert index.auth is not None
        assert isinstance(index.auth, Reference)
        assert index.auth.ref == "test_auth"

    def test_vector_index_embedding_model_string_resolved_to_reference(
        self,
    ) -> None:
        """Test that VectorIndex.embedding_model string is resolved to Reference[EmbeddingModel]."""
        app = load_test_spec(
            "vector_index_embedding_model_reference.qtype.yaml"
        )

        assert app.indexes is not None
        assert len(app.indexes) == 1
        index = app.indexes[0]
        assert isinstance(index, dsl.VectorIndex)

        assert isinstance(index.embedding_model, Reference)
        assert index.embedding_model.ref == "test_embedding_model"


class TestIndexUpsertReferenceResolution:
    """Test reference resolution for IndexUpsert class."""

    def test_index_upsert_string_resolved_to_reference(self) -> None:
        """Test that IndexUpsert.index string is resolved to Reference[IndexType]."""
        app = load_test_spec("index_upsert_reference.qtype.yaml")

        assert app.flows is not None
        flow = app.flows[0]
        step = flow.steps[0]
        assert isinstance(step, dsl.IndexUpsert)

        assert isinstance(step.index, Reference)
        assert step.index.ref == "test_index"


class TestVectorSearchReferenceResolution:
    """Test reference resolution for VectorSearch class (Search base class)."""

    def test_vector_search_index_string_resolved_to_reference(self) -> None:
        """Test that VectorSearch.index string is resolved to Reference[IndexType]."""
        app = load_test_spec("vector_search_index_reference.qtype.yaml")

        assert app.flows is not None
        flow = app.flows[0]
        step = flow.steps[0]
        assert isinstance(step, dsl.VectorSearch)

        assert isinstance(step.index, Reference)
        assert step.index.ref == "search_index"


class TestSecretManagerReferenceResolution:
    """Test reference resolution for SecretManager class."""

    def test_secret_manager_auth_string_resolved_to_reference(self) -> None:
        """Test that SecretManager.auth string is resolved to Reference[AuthProviderType]."""
        app = load_test_spec("secret_manager_with_references.qtype.yaml")

        # Verify secret_manager is configured
        assert app.secret_manager is not None
        assert isinstance(app.secret_manager, dsl.AWSSecretManager)
        assert app.secret_manager.id == "main_secret_manager"

        # Verify the secret_manager auth is a Reference
        assert isinstance(app.secret_manager.auth, Reference)
        assert app.secret_manager.auth.ref == "aws_auth"

        # Verify auth providers with SecretReference fields
        assert app.auths is not None
        assert len(app.auths) == 4

        # Check AWS auth provider with SecretReference fields
        aws_auth = app.auths[0]
        assert isinstance(aws_auth, dsl.AWSAuthProvider)
        assert isinstance(aws_auth.access_key_id, dsl.SecretReference)
        assert aws_auth.access_key_id.secret_name == "my-app/aws-credentials"
        assert aws_auth.access_key_id.key == "access_key_id"

        # Check API key auth provider with SecretReference
        openai_auth = app.auths[1]
        assert isinstance(openai_auth, dsl.APIKeyAuthProvider)
        assert isinstance(openai_auth.api_key, dsl.SecretReference)
        assert openai_auth.api_key.secret_name == "my-app/openai-api-key"
        assert openai_auth.api_key.key is None  # Plain secret, no key

        # Check Bearer token auth provider with SecretReference
        github_auth = app.auths[2]
        assert isinstance(github_auth, dsl.BearerTokenAuthProvider)
        assert isinstance(github_auth.token, dsl.SecretReference)
        assert github_auth.token.secret_name == "my-app/github-tokens"
        assert github_auth.token.key == "personal_access_token"

        # Check OAuth2 auth provider with SecretReference
        oauth_auth = app.auths[3]
        assert isinstance(oauth_auth, dsl.OAuth2AuthProvider)
        assert oauth_auth.client_id == "my-client-id"  # Plain string
        assert isinstance(oauth_auth.client_secret, dsl.SecretReference)
        assert oauth_auth.client_secret.secret_name == "my-app/oauth-secrets"
        assert oauth_auth.client_secret.key == "client_secret"


class TestCombinedReferenceResolution:
    """Test files that combine multiple reference types in one spec."""

    def test_llm_inference_combined_references(self) -> None:
        """Test that LLMInference.model and .memory both resolve in same spec."""
        app = load_test_spec("llm_inference_references.qtype.yaml")

        assert app.flows is not None
        flow = app.flows[0]
        step = flow.steps[0]
        assert isinstance(step, dsl.LLMInference)

        # Both model and memory should be References
        assert isinstance(step.model, Reference)
        assert step.model.ref == "test_model"

        assert step.memory is not None
        assert isinstance(step.memory, Reference)
        assert step.memory.ref == "test_memory"

    def test_step_inputs_outputs_combined_references(self) -> None:
        """Test that Step.inputs and .outputs both resolve in same spec."""
        app = load_test_spec("step_inputs_outputs_reference.qtype.yaml")

        assert app.flows is not None
        flow = app.flows[0]
        step = flow.steps[0]
        assert isinstance(step, dsl.Step)

        # Both inputs and outputs should have References
        assert step.inputs is not None
        assert len(step.inputs) == 1
        assert isinstance(step.inputs[0], Reference)
        assert step.inputs[0].ref == "input_var"

        assert step.outputs is not None
        assert len(step.outputs) == 1
        assert isinstance(step.outputs[0], Reference)
        assert step.outputs[0].ref == "output_var"

    def test_vector_index_combined_references(self) -> None:
        """Test that VectorIndex.auth and .embedding_model both resolve in same spec."""
        app = load_test_spec("vector_index_references.qtype.yaml")

        assert app.indexes is not None
        assert len(app.indexes) == 1
        index = app.indexes[0]
        assert isinstance(index, dsl.VectorIndex)

        # Both auth and embedding_model should be References
        assert index.auth is not None
        assert isinstance(index.auth, Reference)
        assert index.auth.ref == "index_auth"

        assert isinstance(index.embedding_model, Reference)
        assert index.embedding_model.ref == "embedding_model"

    def test_flow_interface_session_inputs_multiple_references(self) -> None:
        """Test that FlowInterface.session_inputs with multiple strings all resolve."""
        app = load_test_spec("flow_interface_session_inputs.qtype.yaml")

        assert app.flows is not None
        flow = app.flows[0]
        assert flow.interface is not None

        # Should have 2 session_inputs, both References
        assert len(flow.interface.session_inputs) == 2
        assert isinstance(flow.interface.session_inputs[0], Reference)
        assert flow.interface.session_inputs[0].ref == "user_name"
        assert isinstance(flow.interface.session_inputs[1], Reference)
        assert flow.interface.session_inputs[1].ref == "user_email"
