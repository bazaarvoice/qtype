"use client";

import { ScrollArea } from "@radix-ui/react-scroll-area";
import { useState } from "react";

import { formatFlowName } from "@/components/FlowTabsContainer";
import { Alert, AlertDescription } from "@/components/ui/Alert";
import { Button } from "@/components/ui/Button";
import { apiClient } from "@/lib/apiClient";

import { useFlowStreaming } from "../../hooks/useFlowStreaming";
import ThinkingPanel from "../chat/ThinkingPanel";
import FlowInputs from "../FlowInputs";
import { MarkdownContainer } from "../MarkdownContainer";

import type { ToolEvent } from "../../hooks/useFlowStreaming";
import type { FlowMetadata, FlowInputValues } from "@/types";

interface StreamFlowProps {
  flow: FlowMetadata;
}

function StreamFlow({ flow }: StreamFlowProps) {
  const path = flow.endpoints.stream;
  const name = formatFlowName(flow.id);
  const description = flow.description;
  const requestSchema = flow.input_schema as Record<string, unknown>;
  const [inputs, setInputs] = useState<FlowInputValues>({});
  const [error, setError] = useState<string | null>(null);

  const streamingEndpoint = `${apiClient.getBaseUrl().replace(/\/$/, "")}${path}`;

  const {
    answer,
    reasoning,
    statusMsg,
    toolEvents,
    isStreaming,
    error: streamError,
    abortStreaming,
    startFromInputs,
  } = useFlowStreaming(streamingEndpoint);

  const handleInputChange = (newInputs: FlowInputValues) =>
    setInputs(newInputs);

  const handleExecute = async () => {
    setError(null);
    const validationError = await startFromInputs(inputs);
    if (validationError) setError(validationError);
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
        <Button disabled={isStreaming} onClick={handleExecute}>
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
        {streamError && (
          <Alert variant="destructive" className="mb-4">
            <AlertDescription className="whitespace-pre-line">
              {streamError}
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
                    {toolEvents.map((t: ToolEvent) => (
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
