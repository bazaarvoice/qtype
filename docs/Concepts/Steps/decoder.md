# Decoder

Decoder steps parse and extract structured data from unstructured text, converting raw content into organized formats like JSON, XML, or custom data structures. They enable applications to transform natural language responses, documents, and other text sources into machine-readable formats for further processing.

Decoders are essential for building robust data pipelines that can handle the variability of AI-generated content and extract actionable information from diverse text sources.

## Rules and Behaviors

- **Format Specification**: Decoders must specify the target output format (JSON, XML, CSV, etc.)
- **Schema Validation**: Output can be validated against predefined schemas to ensure data quality
- **Error Handling**: Decoders handle malformed input gracefully with configurable error strategies
- **Type Conversion**: Automatic conversion of extracted values to appropriate data types
- **Flexible Parsing**: Support for both strict and lenient parsing modes
- **Pattern Matching**: Can use regular expressions or custom patterns for extraction
- **Fallback Strategies**: Configurable behavior when parsing fails (return empty, use defaults, raise error)

## Component Definition

--8<-- "components/Decoder.md"

## Configuration Options

### JSON Decoder

```yaml
steps:
  - id: extract_json
    type: Decoder
    format: json
    inputs:
      - id: raw_text
        type: text
    outputs:
      - id: structured_data
        type: text
    schema:
      type: object
      properties:
        name:
          type: string
        age:
          type: integer
        skills:
          type: array
          items:
            type: string
    strict_mode: true
```

### XML Decoder

```yaml
steps:
  - id: parse_xml
    type: Decoder
    format: xml
    inputs:
      - id: xml_content
        type: text
    outputs:
      - id: parsed_data
        type: text
    root_element: "document"
    namespace_aware: true
```

### Custom Pattern Decoder

```yaml
steps:
  - id: extract_entities
    type: Decoder
    format: custom
    inputs:
      - id: text_content
        type: text
    outputs:
      - id: extracted_entities
        type: text
    patterns:
      - name: "email"
        regex: "\\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\\.[A-Z|a-z]{2,}\\b"
      - name: "phone"
        regex: "\\+?1?\\d{9,15}"
      - name: "date"
        regex: "\\d{4}-\\d{2}-\\d{2}"
```

## Format Types

### JSON Format
- **Purpose**: Extract JSON objects from text
- **Use Cases**: API responses, structured AI outputs, configuration parsing
- **Validation**: Schema-based validation with JSONSchema
- **Error Handling**: Syntax error recovery and partial extraction

### XML Format
- **Purpose**: Parse XML documents and extract elements
- **Use Cases**: Document processing, legacy system integration, structured markup
- **Features**: Namespace support, XPath queries, attribute extraction
- **Output**: Converted to JSON structure or custom format

### CSV Format
- **Purpose**: Parse comma-separated values
- **Use Cases**: Data imports, spreadsheet processing, tabular data extraction
- **Options**: Custom delimiters, header detection, type inference
- **Output**: Array of objects or structured table format

### Custom Format
- **Purpose**: Pattern-based extraction using regular expressions
- **Use Cases**: Entity extraction, log parsing, custom data formats
- **Features**: Named capture groups, multiple patterns, validation rules
- **Output**: Dictionary of extracted values

## Related Concepts

Decoder steps often process outputs from [LLMInference](llm-inference.md) or [Agent](agent.md) steps, work within [Flows](../Concepts/flow.md) for data transformation pipelines, and may validate extracted data against [Variable](../Concepts/variable.md) type definitions. They integrate with other [Steps](../Concepts/step.md) for comprehensive data processing workflows.

## Example Usage

### Basic JSON Extraction

```yaml
id: json_extraction_demo

flows:
  - id: extract_user_data
    steps:
      - id: generate_user_info
        type: LLMInference
        model: gpt-4o
        system_message: "Generate user information in JSON format with name, age, and skills."
        inputs:
          - id: user_description
            type: text
        outputs:
          - id: raw_response
            type: text
      
      - id: parse_json
        type: Decoder
        format: json
        inputs:
          - id: llm_output
            type: text
        outputs:
          - id: user_data
            type: text
        schema:
          type: object
          required: ["name", "age"]
          properties:
            name:
              type: string
              minLength: 1
            age:
              type: integer
              minimum: 0
              maximum: 150
            skills:
              type: array
              items:
                type: string
        strict_mode: false
        fallback_strategy: "partial"
```

### Multi-Format Document Processing

```yaml
id: document_processor

flows:
  - id: process_mixed_content
    steps:
      - id: detect_format
        type: PythonFunctionTool
        module_path: "format_utils"
        function_name: "detect_content_type"
        inputs:
          - id: raw_content
            type: text
        outputs:
          - id: content_type
            type: text
      
      - id: route_by_format
        type: Condition
        inputs:
          - id: format_type
            type: text
        equals:
          id: json_format
          type: text
        then:
          id: decode_json
          type: Decoder
          format: json
          inputs:
            - id: content
              type: text
          outputs:
            - id: structured_output
              type: text
        else:
          id: decode_xml
          type: Decoder
          format: xml
          inputs:
            - id: content
              type: text
          outputs:
            - id: structured_output
              type: text
          root_element: "data"
```

### Entity Extraction Pipeline

```yaml
id: entity_extraction

flows:
  - id: extract_and_validate
    steps:
      - id: extract_entities
        type: Decoder
        format: custom
        inputs:
          - id: document_text
            type: text
        outputs:
          - id: raw_entities
            type: text
        patterns:
          - name: "person"
            regex: "\\b[A-Z][a-z]+ [A-Z][a-z]+\\b"
          - name: "organization"
            regex: "\\b[A-Z][a-zA-Z\\s&]+ (Inc|Corp|LLC|Ltd)\\.?\\b"
          - name: "location"
            regex: "\\b[A-Z][a-z]+(?:,\\s*[A-Z]{2})?\\b"
          - name: "email"
            regex: "\\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\\.[A-Z|a-z]{2,}\\b"
      
      - id: validate_entities
        type: LLMInference
        model: gpt-4o-mini
        system_message: "Validate and categorize the extracted entities. Return JSON with validated entities."
        inputs:
          - id: extracted_data
            type: text
          - id: original_text
            type: text
        outputs:
          - id: validation_result
            type: text
      
      - id: parse_validation
        type: Decoder
        format: json
        inputs:
          - id: validation_json
            type: text
        outputs:
          - id: final_entities
            type: text
        schema:
          type: object
          properties:
            persons:
              type: array
              items:
                type: object
                properties:
                  name:
                    type: string
                  confidence:
                    type: number
                    minimum: 0
                    maximum: 1
            organizations:
              type: array
              items:
                type: object
                properties:
                  name:
                    type: string
                  type:
                    type: string
                  confidence:
                    type: number
```

### Error-Resilient Parsing

```yaml
id: robust_parsing

flows:
  - id: parse_with_fallbacks
    steps:
      - id: attempt_strict_parsing
        type: Decoder
        format: json
        inputs:
          - id: potentially_malformed_json
            type: text
        outputs:
          - id: strict_result
            type: text
        strict_mode: true
        fallback_strategy: "error"
      
      - id: handle_parse_errors
        type: Condition
        inputs:
          - id: parse_status
            type: text
        equals:
          id: success_status
          type: text
        then:
          id: use_strict_result
          type: PythonFunctionTool
          module_path: "data_utils"
          function_name: "format_output"
          inputs:
            - id: parsed_data
              type: text
        else:
          id: lenient_parsing
          type: Decoder
          format: json
          inputs:
            - id: malformed_content
              type: text
          outputs:
            - id: partial_result
              type: text
          strict_mode: false
          fallback_strategy: "partial"
          repair_attempts: 3
      
      - id: clean_and_validate
        type: PythonFunctionTool
        module_path: "data_utils"
        function_name: "clean_and_validate_data"
        inputs:
          - id: raw_parsed_data
            type: text
        outputs:
          - id: clean_data
            type: text
```

### Structured Data Transformation

```yaml
id: data_transformation

flows:
  - id: transform_formats
    steps:
      - id: parse_csv_input
        type: Decoder
        format: csv
        inputs:
          - id: csv_data
            type: text
        outputs:
          - id: tabular_data
            type: text
        delimiter: ","
        has_header: true
        infer_types: true
      
      - id: convert_to_json
        type: PythonFunctionTool
        module_path: "converters"
        function_name: "csv_to_json"
        inputs:
          - id: table_data
            type: text
        outputs:
          - id: json_representation
            type: text
      
      - id: validate_json_structure
        type: Decoder
        format: json
        inputs:
          - id: converted_json
            type: text
        outputs:
          - id: validated_json
            type: text
        schema:
          type: array
          items:
            type: object
            additionalProperties: true
        strict_mode: true
      
      - id: generate_xml_output
        type: PythonFunctionTool
        module_path: "converters"
        function_name: "json_to_xml"
        inputs:
          - id: json_data
            type: text
        outputs:
          - id: xml_output
            type: text
```
