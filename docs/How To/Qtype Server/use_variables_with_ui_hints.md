# Use Variables with UI Hints

Customize how input variables are displayed in the web UI using the `ui` field on variable definitions.

### QType YAML

```yaml
flows:
  - type: Flow
    id: generate_story
    
    variables:
      # Use textarea widget for multi-line text input
      - id: story_prompt
        type: text
        ui:
          widget: textarea
      
      # Use file upload widget with mime type filtering
      - id: document
        type: file
        ui:
          accept: "application/pdf"
      
      # Variables without ui hints use default widgets
      - id: max_length
        type: int
```

### Explanation

- **ui.widget**: For `text` variables, controls input style (`text` for single-line, `textarea` for multi-line)
- **ui.accept**: For `file` variables, specifies accepted mime types (e.g., `"application/pdf"`, `"image/*"`, `"*/*"`)
- **Default widgets**: Variables without `ui` hints automatically use appropriate widgets based on their type

**Note**: UI hints are currently limited to text and file input customization. Other variable types use standard widgets.

## Complete Example

```yaml
--8<-- "../examples/language_features/ui_hints.qtype.yaml"
```

## See Also

- [Serve Flows as UI](serve_flows_as_ui.md)
- [Variable Reference](../../components/Variable.md)
- [Use Optional Variables](../Language%20Features/use_optional_variables.md)
