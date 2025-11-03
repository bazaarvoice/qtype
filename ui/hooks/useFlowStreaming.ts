import { useState, useRef, useCallback } from "react";

export interface ToolEvent {
  id: string;
  type: string;
  text?: string;
  errorText?: string;
}

interface UseFlowStreamingResult {
  answer: string;
  reasoning: string;
  statusMsg: string | null;
  toolEvents: ToolEvent[];
  isStreaming: boolean;
  error: string | null;
  startStreaming: (question: string) => Promise<void>;
  abortStreaming: () => void;
  reset: () => void;
  startFromInputs: (inputs: Record<string, unknown>) => Promise<string | null>;
}

export function useFlowStreaming(endpoint: string): UseFlowStreamingResult {
  const [answer, setAnswer] = useState("");
  const [reasoning, setReasoning] = useState("");
  const [statusMsg, setStatusMsg] = useState<string | null>(null);
  const [toolEvents, setToolEvents] = useState<ToolEvent[]>([]);
  const [isStreaming, setIsStreaming] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const abortRef = useRef<AbortController | null>(null);

  const reset = useCallback(() => {
    setAnswer("");
    setReasoning("");
    setToolEvents([]);
    setStatusMsg(null);
    setError(null);
  }, []);

  const parseSSELine = useCallback((line: string) => {
    if (!line.startsWith("data:")) return;
    const payloadStr = line.slice(5).trim();
    if (!payloadStr || payloadStr === "[DONE]") return;
    let evt: Record<string, unknown>;
    try {
      evt = JSON.parse(payloadStr) as Record<string, unknown>;
    } catch {
      return;
    }
    const type = String(evt.type || "");
    switch (type) {
      case "start-step": {
        setStatusMsg("Starting step...");
        break;
      }
      case "message-metadata": {
        const mm = evt.messageMetadata as Record<string, unknown> | undefined;
        const status =
          mm && typeof mm.statusMessage === "string" ? mm.statusMessage : null;
        if (status) setStatusMsg(status);
        break;
      }
      case "reasoning-start": {
        setReasoning("");
        setStatusMsg("Thinking...");
        break;
      }
      case "reasoning-delta": {
        const delta = typeof evt.delta === "string" ? evt.delta : "";
        if (delta) setReasoning((r) => r + delta);
        setStatusMsg((s) =>
          s && s.startsWith("Thinking") ? s : "Thinking...",
        );
        break;
      }
      case "reasoning-end": {
        setStatusMsg("Finished thinking");
        break;
      }
      case "text-start": {
        setAnswer("");
        break;
      }
      case "text-delta": {
        const delta = typeof evt.delta === "string" ? evt.delta : "";
        if (delta) setAnswer((a) => a + delta);
        break;
      }
      case "tool-input-start":
      case "tool-input-delta":
      case "tool-input-end":
      case "tool-output-available":
      case "tool-output-error": {
        const id =
          (typeof evt.toolCallId === "string" && evt.toolCallId) ||
          (typeof evt.id === "string" && evt.id) ||
          crypto.randomUUID();
        const text =
          typeof evt.delta === "string"
            ? evt.delta
            : typeof evt.output === "string"
              ? evt.output
              : undefined;
        const errorText =
          typeof evt.errorText === "string" ? evt.errorText : undefined;
        setToolEvents((events) => [...events, { id, type, text, errorText }]);
        break;
      }
      case "error": {
        setStatusMsg("Error during streaming");
        break;
      }
      case "finish-step": {
        setStatusMsg("Step finished");
        break;
      }
      case "finish": {
        setStatusMsg("Finished");
        setIsStreaming(false);
        break;
      }
      default: {
        break;
      }
    }
  }, []);

  const startStreaming = useCallback(
    async (question: string) => {
      reset();
      setStatusMsg("Starting...");
      setIsStreaming(true);
      abortRef.current?.abort();
      const controller = new AbortController();
      abortRef.current = controller;
      try {
        const res = await fetch(endpoint, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ prompt: question }),
          signal: controller.signal,
        });
        if (!res.ok || !res.body) throw new Error(`HTTP ${res.status}`);
        const reader = res.body.getReader();
        const decoder = new TextDecoder("utf-8");
        let buffer = "";
        while (true) {
          const { done, value } = await reader.read();
          if (done) break;
          buffer += decoder.decode(value, { stream: true });
          const lines = buffer.split(/\r?\n/);
          buffer = lines.pop() || "";
          for (const l of lines) parseSSELine(l);
        }
        if (buffer) parseSSELine(buffer);
      } catch (e: unknown) {
        const msg = e instanceof Error ? e.message : "Streaming failed";
        setError(msg);
      } finally {
        setIsStreaming(false);
      }
    },
    [endpoint, parseSSELine, reset],
  );

  const startFromInputs = useCallback(
    async (inputs: Record<string, unknown>) => {
      let q = "";
      if ("question" in inputs) {
        q = String(inputs.question ?? "");
      } else {
        const keys = Object.keys(inputs);
        if (keys.length === 1) q = String(inputs[keys[0]] ?? "");
      }
      q = q.trim();
      if (!q) return "Provide a 'question' input (or a single input field).";
      await startStreaming(q);
      return null;
    },
    [startStreaming],
  );

  const abortStreaming = useCallback(() => {
    abortRef.current?.abort();
    setIsStreaming(false);
    setStatusMsg("Aborted");
  }, []);

  return {
    answer,
    reasoning,
    statusMsg,
    toolEvents,
    isStreaming,
    error,
    startStreaming,
    abortStreaming,
    reset,
    startFromInputs,
  };
}
