/**
 * Flow Component
 *
 * Interactive interface for executing a single flow
 */

"use client";

import { LayoutGrid, Table as TableIcon } from "lucide-react";
import { useEffect, useState } from "react";

import { formatFlowName } from "@/components/FlowTabsContainer";
import { Alert, AlertDescription } from "@/components/ui/Alert";
import { Button } from "@/components/ui/Button";
import { apiClient, ApiClientError } from "@/lib/apiClient";

import FlowInputs from "../FlowInputs";
import FlowResponseCard from "../FlowResponseCard";
import FlowResponseTable from "../FlowResponseTable";

import type { FlowMetadata, FlowInputValues, ResponseData } from "@/types";

type ViewMode = "card" | "table";

interface FlowProps {
  flow: FlowMetadata;
}

function RestFlow({ flow }: FlowProps) {
  const path = flow.endpoints.rest;
  const name = formatFlowName(flow.id);
  const description = flow.description;
  const requestSchema = flow.input_schema as Record<string, unknown>;
  const [inputs, setInputs] = useState<FlowInputValues>({});
  const [isExecuting, setIsExecuting] = useState(false);
  const [responseData, setResponseData] = useState<{
    outputs: ResponseData[];
    errors: Array<Record<string, unknown>>;
  } | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [showInput, setShowInput] = useState(true);
  const [viewMode, setViewMode] = useState<ViewMode>(() => {
    if (typeof window === "undefined") return "card";
    const stored = localStorage.getItem("flowResponseViewMode");
    return stored === "table" ? "table" : "card";
  });

  useEffect(() => {
    if (!responseData?.outputs) return;
    if (typeof window === "undefined") return;

    const stored = localStorage.getItem("flowResponseViewMode");
    if (!stored) {
      const defaultMode = responseData.outputs.length > 5 ? "table" : "card";
      setViewMode(defaultMode);
    }
  }, [responseData?.outputs]);

  const handleViewModeChange = (mode: ViewMode) => {
    setViewMode(mode);
    if (typeof window !== "undefined") {
      localStorage.setItem("flowResponseViewMode", mode);
    }
  };

  const handleInputChange = (newInputs: FlowInputValues) => {
    setInputs(newInputs);
  };

  const handleReset = () => {
    setShowInput(true);
    handleInputChange({});
  };

  const executeFlow = async () => {
    setShowInput(false);
    setIsExecuting(true);
    setError(null);
    setResponseData(null);

    try {
      const responseData = await apiClient.executeFlow(path, inputs);
      setResponseData(
        responseData as {
          outputs: ResponseData[];
          errors: Array<Record<string, unknown>>;
        },
      );
    } catch (err) {
      if (err instanceof ApiClientError) {
        setError(err.message);
      } else {
        setError(
          err instanceof Error ? err.message : "An unknown error occurred",
        );
      }
    } finally {
      setIsExecuting(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Flow Header */}
      <div className="border-b pb-4">
        <h3 className="text-xl font-semibold text-gray-900 dark:text-white">
          {name}
        </h3>
        <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
          {path} • POST
        </p>
        {description && (
          <p className="text-gray-600 dark:text-gray-300 mt-2">{description}</p>
        )}
      </div>
      {showInput && (
        <FlowInputs
          requestSchema={requestSchema || null}
          onInputChange={handleInputChange}
        />
      )}

      {showInput && (
        <div className="mt-6 pt-4 border-t">
          <Button
            disabled={isExecuting || !Object.keys(inputs).length}
            onClick={executeFlow}
          >
            Execute Flow
          </Button>
        </div>
      )}

      <div>
        {isExecuting && !showInput && (
          <div className="flex items-center justify-center py-12">
            <div className="text-gray-500 dark:text-gray-400">Executing...</div>
          </div>
        )}

        {error && (
          <Alert variant="destructive" className="mb-4">
            <AlertDescription>
              <div className="whitespace-pre-line">
                <span className="font-medium">Error:</span>
                <br />
                {error}
              </div>
            </AlertDescription>
          </Alert>
        )}

        {responseData && (
          <div className="space-y-4">
            {/* Show errors if any */}
            {responseData.errors && responseData.errors.length > 0 && (
              <div className="space-y-2">
                <h4 className="text-sm font-semibold text-red-600 dark:text-red-400">
                  Errors ({responseData.errors.length})
                </h4>
                {responseData.errors.map((errorItem, idx) => (
                  <Alert key={idx} variant="destructive">
                    <AlertDescription>
                      <pre className="text-xs whitespace-pre-wrap">
                        {JSON.stringify(errorItem, null, 2)}
                      </pre>
                    </AlertDescription>
                  </Alert>
                ))}
              </div>
            )}

            {/* Show outputs if any */}
            {responseData.outputs &&
              responseData.outputs.length > 0 &&
              !showInput && (
                <div className="space-y-4">
                  <div className="flex items-center justify-between">
                    <h4 className="text-sm font-semibold text-gray-700 dark:text-gray-300">
                      Outputs ({responseData.outputs.length})
                    </h4>
                    <div
                      className="inline-flex rounded-md shadow-sm"
                      role="group"
                    >
                      <Button
                        variant={viewMode === "card" ? "default" : "outline"}
                        size="sm"
                        onClick={() => handleViewModeChange("card")}
                        className="rounded-r-none"
                      >
                        <LayoutGrid className="h-4 w-4 mr-2" />
                        Cards
                      </Button>
                      <Button
                        variant={viewMode === "table" ? "default" : "outline"}
                        size="sm"
                        onClick={() => handleViewModeChange("table")}
                        className="rounded-l-none"
                      >
                        <TableIcon className="h-4 w-4 mr-2" />
                        Table
                      </Button>
                    </div>
                  </div>

                  {viewMode === "card" ? (
                    <div className="space-y-4">
                      {responseData.outputs.map((output, idx) => (
                        <div
                          key={idx}
                          className="border border-gray-200 dark:border-gray-700 rounded-lg p-4"
                        >
                          {responseData.outputs.length > 1 && (
                            <div className="text-xs text-gray-500 dark:text-gray-400 mb-2">
                              Result {idx + 1}
                            </div>
                          )}

                          <FlowResponseCard
                            responseSchema={flow.output_schema}
                            responseData={output}
                            feedbackConfig={flow.feedback}
                            telemetryEnabled={flow.telemetry_enabled}
                          />
                        </div>
                      ))}
                    </div>
                  ) : (
                    <FlowResponseTable
                      responseSchema={flow.output_schema}
                      outputs={responseData.outputs}
                      feedbackConfig={flow.feedback}
                      telemetryEnabled={flow.telemetry_enabled}
                    />
                  )}
                </div>
              )}

            {/* Show message if no outputs and no errors */}
            {(!responseData.outputs || responseData.outputs.length === 0) &&
              (!responseData.errors || responseData.errors.length === 0) && (
                <div className="text-gray-500 dark:text-gray-400 text-sm">
                  No results returned
                </div>
              )}
          </div>
        )}
      </div>

      {!showInput && (
        <div className="mt-6 pt-4 border-t">
          <Button disabled={isExecuting} onClick={handleReset}>
            Reset
          </Button>
        </div>
      )}
    </div>
  );
}

export { RestFlow };
