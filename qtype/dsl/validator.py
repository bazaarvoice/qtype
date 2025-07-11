from argparse import Namespace

from qtype.dsl.model import Document
from qtype.parser.loader import load_yaml


def validate_spec(args: Namespace) -> Document:
    """Validate a QType YAML spec file against the Document schema."""
    data = load_yaml(args.spec)
    return Document.model_validate(data)
