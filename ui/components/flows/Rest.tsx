/**
 * Flow Component
 *
 * Interactive interface for executing a single flow
 */

"use client";

import { useState } from "react";

import { formatFlowName } from "@/components/FlowTabsContainer";
import { Alert, AlertDescription } from "@/components/ui/Alert";
import { Button } from "@/components/ui/Button";
import { apiClient, ApiClientError } from "@/lib/apiClient";

import FlowInputs from "../FlowInputs";
import FlowResponse from "../FlowResponse";

import type { FlowMetadata, FlowInputValues, ResponseData } from "@/types";

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

  const handleInputChange = (newInputs: FlowInputValues) => {
    setInputs(newInputs);
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
      <div className="mt-6 pt-4 border-t">
        {!showInput ? (
          <Button disabled={isExecuting} onClick={() => setShowInput(true)}>
            Reset
          </Button>
        ) : (
          <Button disabled={isExecuting} onClick={executeFlow}>
            {isExecuting ? "Executing..." : "Execute Flow"}
          </Button>
        )}
      </div>

      <div>
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
                  <h4 className="text-sm font-semibold text-gray-700 dark:text-gray-300">
                    Outputs ({responseData.outputs.length})
                  </h4>
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

                      <FlowResponse
                        responseSchema={flow.output_schema}
                        responseData={output}
                      />
                    </div>
                  ))}
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
    </div>
  );
}

export { RestFlow };
