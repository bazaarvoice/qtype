import argparse
import json
from typing import Optional

from qtype.dsl.model import Document


def generate_schema_main(args: argparse.Namespace) -> None:
    """Generate and output the JSON schema for Document.

    Args:
        args (argparse.Namespace): Command-line arguments with an optional
            'output' attribute specifying the output file path.
    """
    schema = Document.model_json_schema()
    # Add the $schema property to indicate JSON Schema version
    schema["$schema"] = "http://json-schema.org/draft-07/schema#"
    output = json.dumps(schema, indent=2)
    output_path: Optional[str] = getattr(args, "output", None)
    if output_path:
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(output)
    else:
        print(output)
