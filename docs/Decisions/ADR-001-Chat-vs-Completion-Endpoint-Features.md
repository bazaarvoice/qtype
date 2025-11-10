# ADR 001: Separation of Features Between Chat and Completion Endpoints

* **Status:** Accepted
* **Date:** 2025-11-04
* **Approved by:** Lou Kratz

---

## Context

We offer two primary LLM endpoints: `/chat` and `/completion`, both with streaming and non-streaming (REST) variants. We needed to decide where to return advanced features (like `reasoning`, `tool_calls`, etc.) versus simple text-deltas.

The `/completion` endpoint was beginning to accumulate complex features, which conflicts with its intended simple (prompt-in, text-out) purpose. This created friction with frontend libraries like Vercel's AI SDK, whose `useCompletion` hook is designed to handle only a simple string/text-delta stream.

## Decision

We will strictly separate the concerns of the two endpoints to align with industry best practices and simplify their use:

1.  **`/chat` (Stream):** This will be the **only** endpoint that returns advanced features (e.g., `reasoning`, `tool_calls`, and other non-text metadata).
2.  **`/completion` (Stream & REST):** These endpoints will **only** return simple text. The stream will only contain text-deltas, and the REST endpoint will return the final completed text string.
3.  **`/chat` (REST):** This endpoint will also return simple text responses, consistent with the other REST endpoints.

All advanced functionality will be removed from the `/completion` endpoints and the non-streaming `/chat` endpoint.

---

## Consequences

### Positive

* **Simplicity & Alignment:** This aligns the `/completion` endpoint with its intended purpose as a simple Q&A/generation tool. It matches the pattern set by major libraries (like Vercel's SDK), which treat "completion" as a simple string.
* **Improved FE Integration:** Our UIs can now use the standard `useCompletion` hook directly without any workarounds.
* **Clear API Contract:** 3rd-party developers have a clear choice:
    * Use `/completion` for simple text generation.
    * Use `/chat` (stream) for complex, stateful, or tool-enabled interactions.
* **Long-Term Maintainability:** We only need to build, test, and maintain advanced features in a single endpoint (the chat stream), reducing complexity.

### Negative

* (None identified; this decision is considered a simplification and correction of a previous design.)

---

## Options Considered

### Option 1: Keep `useCompletion` and Manually Parse Data

* **Details:** Keep using the Vercel `useCompletion` hook in the frontend but change our stream protocol to `text` (from the default). We would then manually embed JSON for `reasoning`/`tools` within the text stream and parse it on the client.
* **Rejected Because:** This requires complex, brittle, and manual handling of stream states and data extraction in the frontend, defeating the purpose of using the simple hook.

### Option 2: Use `useChat` for the Completion UI

* **Details:** Have our simple "completion" UI use the `/chat` endpoint and Vercel's `useChat` hook, but always send an empty message array.
* **Rejected Because:**
    1.  **Poor FE Experience:** It complicates the frontend logic, requiring us to manually clear Vercel's `messages` state after every single request.
    2.  **Poor API Experience:** It forces 3rd-party users (who just want to send a simple prompt) to use the more complex `/chat` object format instead of the simple `/completion` string format.