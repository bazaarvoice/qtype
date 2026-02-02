# Decode JSON/XML to Structured Data

Parse string data in JSON or XML format into structured outputs. This is particularly useful for extracting structured data from llm outputs.

### QType YAML

```yaml
--8<-- "../examples/data_processing/decode_json.qtype.yaml"
```

### Explanation

- **Decoder**: Step that parses string data (JSON or XML) into structured outputs
- **format**: The data format to parse - `json` (default) or `xml`
- **inputs**: String variable containing the encoded data to decode
- **outputs**: List of variables to extract from the decoded data (field names must match keys in the JSON/XML)
- **Error handling**: If parsing fails, the step raises returns an error
- **Markdown cleanup**: Automatically strips markdown code fences (```json, ```xml) if present in the input

## See Also

- [Decoder Reference](../../components/Decoder.md)
- [CustomType Reference](../../components/CustomType.md)
- [Tutorial: Structured Data](../../Tutorials/03-structured-data.md)
