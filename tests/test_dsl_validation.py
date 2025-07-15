from __future__ import annotations

import pytest
from pathlib import Path
from typing import Any, Callable
from qtype import dsl
from qtype.dsl import loader, validator

TEST_DIR = Path(__file__).parent / "specs" / "dsl_validate"


def load_application_from_yaml(yaml_path: Path) -> Any:
    """Load a DSL Application from a YAML file."""
    content = yaml_path.read_text(encoding="utf-8")
    return loader.load(content)


def run_validation(yaml_path: Path) -> dsl.Application:
    """Load and validate a DSL Application from a YAML file."""
    app = load_application_from_yaml(yaml_path)
    return validator.validate(app)


@pytest.mark.parametrize(
    "yaml_file",
    [
        "valid_simple_flow.qtype.yaml",
    ],
)
def test_valid_dsl_files(yaml_file: str) -> None:
    """Test that valid DSL YAML files pass validation."""
    yaml_path = TEST_DIR / yaml_file
    run_validation(yaml_path)


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
