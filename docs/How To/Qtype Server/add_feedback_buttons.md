# Add Feedback Buttons

Collect user feedback (thumbs, ratings, or categories) directly in the QType UI by adding a `feedback` block to your flow. Feedback submission requires `telemetry` to be enabled so QType can attach the feedback to traces/spans.

### QType YAML

```yaml
flows:
  - id: my_flow
    interface:
      type: Conversational

    feedback:
      type: thumbs
      explanation: true

telemetry:
  id: app_telemetry
  provider: Phoenix
  endpoint: http://localhost:6006/v1/traces
```

### Explanation

- **flows[].feedback**: Enables a feedback widget on the flow’s outputs in the UI.
- **feedback.type**: Feedback widget type: `thumbs`, `rating`, or `category`.
- **feedback.explanation**: If `true`, prompts the user for an optional text explanation along with their feedback.
- **rating.scale**: For `rating` feedback, sets the maximum score (typically `5` or `10`).
- **category.categories**: For `category` feedback, the list of selectable labels.
- **category.allow_multiple**: For `category` feedback, allows selecting multiple labels.
- **telemetry**: Must be configured for feedback submission; QType records feedback as telemetry annotations.

## See Also

- [Serve Flows as UI](serve_flows_as_ui.md)
- [Use Conversational Interfaces](use_conversational_interfaces.md)
- [TelemetrySink Reference](../../components/TelemetrySink.md)
- [Example: Thumbs Feedback](../../../examples/feedback/thumbs_feedback_example.qtype.yaml)
- [Example: Rating Feedback](../../../examples/feedback/rating_feedback_example.qtype.yaml)
- [Example: Category Feedback](../../../examples/feedback/category_feedback_example.qtype.yaml)
