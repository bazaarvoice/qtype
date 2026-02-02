# Use Conversational Interfaces

The `Conversational` interface tells the QType UI to render a chat instead of just an "execute flow" button.

Note that, if you set the interface to Conversational, QType will validate that the input and outputs are of type `ChatMessage`. If you set the interface to Conversational and this is not true, and error will be thrown.

### QType YAML

```yaml
flows:
  - type: Flow
    id: simple_chat_example
    interface:
      type: Conversational
    variables:
      - id: user_message
        type: ChatMessage
      - id: response_message
        type: ChatMessage
    inputs:
      - user_message
    outputs:
      - response_message
```

### Web UI

When you serve a conversational flow with `qtype serve`, the UI renders a chat interface:

![Chat interface showing conversation with memory](../../Tutorials/example_chat.png)


### Explanation

- **interface.type: Conversational**: Configures the flow to be served as a chat interface in the web UI rather than a simple form
- **ChatMessage type**: Domain type that structures messages with content blocks, role metadata, and conversation context
- **Reset on refresh**: Starting a new browser session creates a new conversation with fresh memory

## Complete Example

```yaml
--8<-- "../examples/tutorials/02_conversational_chat.qtype.yaml"
```

**Start the chat interface:**
```bash
qtype serve 02_conversational_chat.qtype.yaml
```

Visit [http://localhost:8000/ui](http://localhost:8000/ui) to interact with the chatbot.

## See Also

- [Serve Flows as UI](serve_flows_as_ui.md)
- [Tutorial: Conversational Chatbot](../../Tutorials/02-conversational-chatbot.md)
- [ChatMessage Reference](../../components/ChatMessage.md)
