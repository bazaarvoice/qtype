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
