from argparse import Namespace

import yaml

from qtype.dsl.model import QTypeSpec


def validate_spec(args: Namespace) -> QTypeSpec:
    """Validate a QType YAML spec file against the QTypeSpec schema."""
    with open(args.spec, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return QTypeSpec.model_validate(data)
