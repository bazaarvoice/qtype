import json

from qtype.dsl.models import QTypeSpec


def generate_schema_main(args):
    """Generate and output the JSON schema for QTypeSpec."""
    schema = QTypeSpec.model_json_schema()
    output = json.dumps(schema, indent=2)
    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(output)
    else:
        print(output)
