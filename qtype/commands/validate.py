import sys
import yaml
from pydantic import ValidationError
from qtype.dsl.models import QTypeSpec

def validate_main(args):
    """Validate a QType YAML spec file against the QTypeSpec schema."""
    with open(args.spec, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    try:
        QTypeSpec.parse_obj(data)
        print("Validation successful.")
    except ValidationError as e:
        print("Validation failed:")
        print(e)
        sys.exit(1)