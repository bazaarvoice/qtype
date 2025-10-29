from __future__ import annotations

import glob
from pathlib import Path
from typing import Callable

import pytest
from pydantic import BaseModel

from qtype import dsl
from qtype.dsl import linker, loader

TEST_DIR = Path(__file__).parent.parent / "specs"


# There should be no instances of Reference left in the validated model
def has_reference(model: BaseModel) -> bool:
    if isinstance(model, dsl.Reference):
        return True
    if isinstance(model, BaseModel):
        for _, field_value in model.__iter__():
            if has_reference(field_value):
                return True
    elif isinstance(model, list):
        for item in model:
            if has_reference(item):
                return True
    elif isinstance(model, dict):
        for item in model.values():
            if has_reference(item):
                return True
    return False


def run_validation(yaml_path: Path) -> dsl.Application:
    """Load and validate a DSL Application from a YAML file."""
    model, dynamic_types_registry = loader.load_document(yaml_path)
    if not isinstance(model, dsl.Application):
        raise TypeError(f"Expected Application, got {type(model)}")
    app = linker.link(model)
    assert not has_reference(app), "There are unresolved Reference instances"
    return app


@pytest.mark.parametrize(
    "yaml_file",
    [Path(f).name for f in glob.glob(str(TEST_DIR / "valid_*.qtype.yaml"))],
)
def test_valid_dsl_files(yaml_file: str) -> None:
    """Test that valid DSL YAML files pass validation."""
    yaml_path = TEST_DIR / yaml_file
    # should not throw an exception
    run_validation(yaml_path)


@pytest.mark.parametrize(
    "yaml_file,expected_exception",
    [
        ("invalid_repeat_ids.qtype.yaml", linker.DuplicateComponentError),
        # ("invalid_flow_no_steps.qtype.yaml", validator.FlowHasNoStepsError),
        (
            "invalid_reference_not_found.qtype.yaml",
            linker.ReferenceNotFoundError,
        ),
        # (
        #     "invalid_chatflow_no_chatmessage.qtype.yaml",
        #     validator.QTypeValidationError,
        # ),
        (
            "invalid_file_source_no_path.qtype.yaml",
            ValueError,
        ),
        (
            "invalid_file_sink_no_path.qtype.yaml",
            ValueError,
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
    assert not isinstance(component, str), (
        "Component should be resolved to an object"
    )


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
