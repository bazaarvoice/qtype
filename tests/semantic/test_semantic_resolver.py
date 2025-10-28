from __future__ import annotations

from pathlib import Path

from qtype.semantic import loader
from qtype.semantic import model as ir

TEST_DIR = Path(__file__).parent.parent / "specs"


def test_resolver_full_application() -> None:
    """Test resolver.resolve with a fully populated application YAML."""
    yaml_path = TEST_DIR / "full_application_test.qtype.yaml"
    ir_app, dynamic_types = loader.load_from_string(
        yaml_path.read_text(encoding="utf-8"), base_path=yaml_path.parent
    )
    # Application level
    assert isinstance(ir_app, ir.Application)
    assert ir_app.id == "test_app"
    assert (
        ir_app.description == "A test application with all fields populated."
    )
    # Memories
    assert len(ir_app.memories) == 1
    assert ir_app.memories[0].id == "mem1"
    # Models
    assert len(ir_app.models) == 2
    model = ir_app.models[0]
    assert model.id == "model1"
    assert model.provider == "openai"
    assert model.model_id == "gpt-4"
    assert model.inference_params["temperature"] == 0.7
    assert model.inference_params["max_tokens"] == 256
    assert model.auth.id == "auth1"  # type: ignore[union-attr]
    # Flows and steps
    assert len(ir_app.flows) == 1
    flow = ir_app.flows[0]
    assert flow.id == "flow1"
    # Variables are now at flow level
    assert len(flow.variables) == 1
    assert flow.variables[0].id == "var1"
    assert flow.variables[0].type == "text"
    # assert flow.inputs[0].id == "var1"
    # assert flow.outputs[0].id == "var1"
    assert len(flow.steps) == 1
    step = flow.steps[0]
    assert step.id == "step1"
    assert step.inputs[0].id == "var1"
    assert step.outputs[0].id == "var1"
    assert step.model.id == "model1"  # type: ignore[attr-defined]
    assert step.memory.id == "mem1"  # type: ignore[attr-defined]
    assert step.system_message == "Test system message."  # type: ignore[attr-defined]
    assert step.tools[0].id == "tool1"  # type: ignore[attr-defined]
    # Auths
    assert len(ir_app.auths) == 1
    auth = ir_app.auths[0]
    assert auth.id == "auth1"
    assert auth.type == "api_key"
    assert auth.api_key == "secret-key"
    assert auth.host == "https://api.example.com"
    # Tools
    assert len(ir_app.tools) == 1
    tool = ir_app.tools[0]
    assert tool.id == "tool1"
    assert tool.name == "Test Tool"
    assert tool.description == "A tool for testing."
    assert tool.endpoint == "https://api.example.com/test"  # type: ignore[attr-defined]
    assert tool.method == "POST"  # type: ignore[attr-defined]
    assert tool.auth.id == "auth1"  # type: ignore[attr-defined]
    assert tool.headers["Content-Type"] == "application/json"  # type: ignore[attr-defined]
    # Indexes
    assert len(ir_app.indexes) == 1
    index = ir_app.indexes[0]
    assert index.id == "index1"
    assert index.name == "Test Index"
    assert index.embedding_model.id == "embed1"  # type: ignore[attr-defined]
    assert index.args["param"] == "value"
    assert index.auth.id == "auth1"  # type: ignore[union-attr]
    # Telemetry
    assert ir_app.telemetry.id == "telemetry1"  # type: ignore[union-attr]
    assert ir_app.telemetry.endpoint == "https://telemetry.example.com"  # type: ignore[union-attr]
    assert ir_app.telemetry.auth.id == "auth1"  # type: ignore[union-attr]
    # # References
    # assert ir_app.references[0] == "other_app.qtype.yaml"
