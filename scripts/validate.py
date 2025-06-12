# scripts/qtype_cli.py
import argparse
import yaml
import json
from jsonschema import validate, ValidationError
from pathlib import Path

SCHEMA_PATH = Path(__file__).parent.parent / "schema" / "qtype.schema.json"

def main():
    parser = argparse.ArgumentParser(description="Validate QType YAML files against the DSL schema.")
    parser.add_argument("file", help="Path to the .qtype.yaml file")
    args = parser.parse_args()

    try:
        with open(args.file, "r") as f:
            data = yaml.safe_load(f)
        with open(SCHEMA_PATH, "r") as f:
            schema = json.load(f)
        validate(instance=data, schema=schema)
        print("✅ Valid QType YAML file.")
    except FileNotFoundError as e:
        print(f"❌ File not found: {e}")
    except ValidationError as e:
        print(f"❌ Validation failed:\n{e.message}\nAt: {list(e.path)}")
    except Exception as e:
        print(f"❌ Unexpected error:\n{e}")
