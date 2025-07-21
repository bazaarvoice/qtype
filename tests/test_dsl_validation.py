from __future__ import annotations

from pathlib import Path
from typing import Callable

import pytest

from qtype import dsl, loader
from qtype.dsl import validator

TEST_DIR = Path(__file__).parent / "specs"


def run_validation(yaml_path: Path) -> dsl.Application:
    """Load and validate a DSL Application from a YAML file."""
    content = yaml_path.read_text(encoding="utf-8")
    yaml_data = loader.load_yaml(content)
    model = dsl.Document.model_validate(yaml_data).root
    if not isinstance(model, dsl.Application):
        raise TypeError(f"Expected Application, got {type(model)}")
    return validator.validate(model)


@pytest.mark.parametrize(
    "yaml_file",
    [TEST_DIR / "valid_type_list_reference.qtype.yaml"],
    # + [Path(f).name for f in glob.glob(str(TEST_DIR / "valid_*.qtype.yaml"))],
)
def test_valid_dsl_files(yaml_file: str) -> None:
    """Test that valid DSL YAML files pass validation."""
    yaml_path = TEST_DIR / yaml_file
    # should not throw an exception
    app = run_validation(yaml_path)

    # verify that all Nonable components are empty lists
    if not app.auths:
        assert app.auths == []
    if not app.models:
        assert app.models == []
    if not app.indexes:
        assert app.indexes == []
    if not app.tools:
        assert app.tools == []
    if not app.flows:
        assert app.flows == []
    if not app.variables:
        assert app.variables == []
    if not app.references:
        assert app.references == []


@pytest.mark.parametrize(
    "yaml_file,expected_exception",
    [
        ("invalid_repeat_ids.qtype.yaml", validator.DuplicateComponentError),
        ("invalid_flow_no_steps.qtype.yaml", validator.FlowHasNoStepsError),
        (
            "invalid_reference_not_found.qtype.yaml",
            validator.ReferenceNotFoundError,
        ),
    ],
)
def test_invalid_dsl_files(
    yaml_file: str, expected_exception: type[Exception]
) -> None:
    """Test that invalid DSL YAML files raise the expected exception."""
    yaml_path = TEST_DIR / yaml_file
    with pytest.raises(expected_exception):
        run_validation(yaml_path)


@pytest.mark.parametrize(
    "yaml_file,getter",
    [
        (
            "valid_simple_flow_with_reference.qtype.yaml",
            lambda x: x.flows[0].steps[0].inputs[0],
        ),
        (
            "valid_model_auth_reference.qtype.yaml",
            lambda x: x.models[0].auth,
        ),
        (
            "valid_llm_memory_reference.qtype.yaml",
            lambda x: x.flows[0].steps[0].memory,
        ),
        (
            "valid_vectorindex_embedding_reference.qtype.yaml",
            lambda x: x.indexes[0].embedding_model,
        ),
        (
            "valid_condition_else_reference.qtype.yaml",
            lambda x: x.flows[0].steps[2].else_,
        ),
        (
            "valid_condition_then_reference.qtype.yaml",
            lambda x: x.flows[0].steps[2].then,
        ),
        (
            "valid_apitool_auth_reference.qtype.yaml",
            lambda x: x.tools[0].auth,
        ),
        (
            "valid_step_inputs_reference.qtype.yaml",
            lambda x: x.flows[0].steps[0].inputs[0],
        ),
        (
            "valid_step_outputs_reference.qtype.yaml",
            lambda x: x.flows[0].steps[0].outputs[0],
        ),
        (
            "valid_telemetrysink_auth_reference.qtype.yaml",
            lambda x: x.telemetry.auth,
        ),
        (
            "valid_agent_tools_reference.qtype.yaml",
            lambda x: x.tools[0],
        ),
        (
            "valid_flow_steps_reference.qtype.yaml",
            lambda x: x.flows[0].steps[0],
        ),
        (
            "valid_flow_steps_reference.qtype.yaml",
            lambda x: x.flows[0].steps[0],
        ),
        ("full_application_test.qtype.yaml", lambda x: x.models[0].auth),
        (
            "full_application_test.qtype.yaml",
            lambda x: x.indexes[0].embedding_model,
        ),
    ],
)
def test_reference_id_resolution(yaml_file: str, getter: Callable) -> None:
    """Test that reference IDs in DSL files are resolved correctly."""
    yaml_path = TEST_DIR / yaml_file
    app = run_validation(yaml_path)
    component = getter(app)
    assert not isinstance(
        component, str
    ), "Component should be resolved to an object"


def test_embedding_model() -> None:
    """Test that the embedding model is correctly defined in the DSL."""
    yaml_path = TEST_DIR / "valid_vectorindex_embedding_reference.qtype.yaml"
    app = run_validation(yaml_path)
    assert app.indexes[0].embedding_model is not None, (  # type: ignore
        "Embedding model should not be None"
    )
    assert isinstance(app.indexes[0].embedding_model, dsl.EmbeddingModel), (  # type: ignore
        "Embedding model should be an instance of EmbeddingModel"
    )
