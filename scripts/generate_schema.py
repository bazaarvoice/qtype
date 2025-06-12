from qtype.dsl.models import QTypeSpec
import json

# Generate schema
schema = QTypeSpec.model_json_schema()

# Save to file
with open("schema/qtype.schema.json", "w") as f:
    json.dump(schema, f, indent=2)

print("✅ QType JSON schema written to schema/qtype.schema.json")
