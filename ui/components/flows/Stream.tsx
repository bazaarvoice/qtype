"use client";

import { ScrollArea } from "@radix-ui/react-scroll-area";
import { useState, useCallback, useRef } from "react";

import { formatFlowName } from "@/components/FlowTabsContainer";
import { Alert, AlertDescription } from "@/components/ui/Alert";
import { Button } from "@/components/ui/Button";
import { apiClient } from "@/lib/apiClient";

import ThinkingPanel from "../chat/ThinkingPanel";
import FlowInputs from "../FlowInputs";
import { MarkdownContainer } from "../MarkdownContainer";

import type { FlowMetadata, FlowInputValues } from "@/types";

interface StreamFlowProps {
  flow: FlowMetadata;
}

interface ToolEvent {
  id: string;
  type: string;
  text?: string;
  errorText?: string;
}

function StreamFlow({ flow }: StreamFlowProps) {
  const path = flow.endpoints.stream;
  const name = formatFlowName(flow.id);
  const description = flow.description;
  const requestSchema = flow.input_schema as Record<string, unknown>;
  const [inputs, setInputs] = useState<FlowInputValues>({});
  const [error, setError] = useState<string | null>(null);

  const streamingEndpoint = `${apiClient.getBaseUrl().replace(/\/$/, "")}${path}`;

  const [answer, setAnswer] = useState("");
  const [reasoning, setReasoning] = useState("");
  const [statusMsg, setStatusMsg] = useState<string | null>(null);
  const [toolEvents, setToolEvents] = useState<ToolEvent[]>([]);
  const [isStreaming, setIsStreaming] = useState(false);
  const abortRef = useRef<AbortController | null>(null);

  const handleInputChange = (newInputs: FlowInputValues) =>
    setInputs(newInputs);

  const extractQuestion = useCallback((): string => {
    if ("question" in inputs) return String(inputs.question ?? "");
    const keys = Object.keys(inputs);

    if (keys.length === 1) return String(inputs[keys[0]] ?? "");
    return "";
  }, [inputs]);

  const parseSSELine = useCallback((line: string) => {
    if (!line.startsWith("data:")) return;
    const payloadStr = line.slice(5).trim();
    if (!payloadStr || payloadStr === "[DONE]") return;
    let evt;
    try {
      evt = JSON.parse(payloadStr);
    } catch {
      return;
    }
    const { type } = evt;
    switch (type) {
      case "start-step":
        setStatusMsg("Starting step...");
        break;
      case "message-metadata":
        if (evt.messageMetadata?.statusMessage) {
          setStatusMsg(evt.messageMetadata.statusMessage);
        }
        break;
      case "reasoning-start":
        setReasoning("");
        setStatusMsg("Thinking...");
        break;
      case "reasoning-delta": {
        const d = evt.delta ?? "";
        if (d) {
          setReasoning((r) => r + d);
          setStatusMsg((s) => (s?.startsWith("Thinking") ? s : "Thinking..."));
        }
        break;
      }
      case "reasoning-end":
        setStatusMsg("Finished thinking");
        break;
      case "text-start":
        setAnswer("");
        break;
      case "text-delta": {
        const d = evt.delta ?? "";
        if (d) setAnswer((a) => a + d);
        break;
      }
      case "tool-input-start":
      case "tool-input-delta":
      case "tool-input-end":
      case "tool-output-available":
      case "tool-output-error": {
        setToolEvents((events) => [
          ...events,
          {
            id: evt.toolCallId || evt.id || crypto.randomUUID(),
            type,
            text: evt.delta || evt.output,
            errorText: evt.errorText,
          },
        ]);
        break;
      }
      case "error":
        setStatusMsg("Error during streaming");
        break;
      case "finish-step":
        setStatusMsg("Step finished");
        break;
      case "finish":
        setStatusMsg("Finished");
        setIsStreaming(false);
        break;
      default:
        break;
    }
  }, []);

  const startStreaming = async () => {
    setError(null);
    const question = extractQuestion().trim();
    if (!question) {
      setError("Provide a 'question' input (or a single input field).");
      return;
    }
    // Reset state
    setAnswer("");
    setReasoning("");
    setToolEvents([]);
    setStatusMsg("Starting...");
    setIsStreaming(true);

    // Abort previous if exists
    abortRef.current?.abort();
    const controller = new AbortController();
    abortRef.current = controller;

    try {
      const res = await fetch(streamingEndpoint, {
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
        buffer = lines.pop() || ""; // keep incomplete
        for (const l of lines) parseSSELine(l);
      }
      if (buffer) parseSSELine(buffer);
    } catch (e) {
      const msg = e instanceof Error ? e.message : "Streaming failed";
      setError(msg);
    } finally {
      setIsStreaming(false);
    }
  };

  const abortStreaming = () => {
    abortRef.current?.abort();
    setIsStreaming(false);
    setStatusMsg("Aborted");
  };

  return (
    <div className="space-y-6">
      <div className="border-b pb-4">
        <h3 className="text-xl font-semibold text-gray-900 dark:text-white">
          {name}
        </h3>
        <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
          {streamingEndpoint} • POST (stream)
        </p>
        {description && (
          <p className="text-gray-600 dark:text-gray-300 mt-2">{description}</p>
        )}
      </div>

      <FlowInputs
        requestSchema={requestSchema || null}
        onInputChange={handleInputChange}
      />
      <div className="mt-6 pt-4 border-t flex flex-wrap gap-2">
        <Button disabled={isStreaming} onClick={startStreaming}>
          {isStreaming ? "Streaming..." : "Execute Flow"}
        </Button>
        {isStreaming && (
          <Button variant="outline" onClick={abortStreaming}>
            Abort
          </Button>
        )}
      </div>

      <div>
        {error && (
          <Alert variant="destructive" className="mb-4">
            <AlertDescription className="whitespace-pre-line">
              {error}
            </AlertDescription>
          </Alert>
        )}
        {(answer || reasoning || toolEvents.length > 0) && (
          <ScrollArea className="flex-1 min-h-0 space-y-4">
            <div className="space-y-3">
              {statusMsg && (
                <div className="text-xs italic text-muted-foreground">
                  {statusMsg}
                </div>
              )}
              <ThinkingPanel reasoningContent={reasoning} />
              {answer && <MarkdownContainer>{answer}</MarkdownContainer>}
              {toolEvents.length > 0 && (
                <div className="mt-4 space-y-2">
                  <h4 className="text-sm font-medium">Tool Events</h4>
                  <ul className="text-xs space-y-1">
                    {toolEvents.map((t) => (
                      <li key={t.id} className="flex gap-2">
                        <span className="font-mono text-[10px] px-1 py-0.5 rounded bg-muted">
                          {t.type}
                        </span>
                        <span className="flex-1 truncate">
                          {t.errorText || t.text || "(no data)"}
                        </span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          </ScrollArea>
        )}
      </div>
    </div>
  );
}

export { StreamFlow };
