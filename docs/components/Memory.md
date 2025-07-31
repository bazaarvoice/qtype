### Memory

Session or persistent memory used to store relevant conversation or state data across steps or turns.

- **id** (`str`): Unique ID of the memory block.
- **token_limit** (`int`): Maximum number of tokens to store in memory.
- **chat_history_token_ratio** (`float`): Ratio of chat history tokens to total memory tokens.
- **token_flush_size** (`int`): Size of memory to flush when it exceeds the token limit.
