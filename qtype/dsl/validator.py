from argparse import Namespace

from qtype.dsl.model import QTypeSpec
from qtype.parser.loader import load_yaml


def validate_spec(args: Namespace) -> QTypeSpec:
    """Validate a QType YAML spec file against the QTypeSpec schema."""
    data = load_yaml(args.spec)
    return QTypeSpec.model_validate(data)
