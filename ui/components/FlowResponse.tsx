/**
 * Flow Response Component
 *
 * Renders flow response data based on response schema
 */

"use client";

import { Alert, AlertDescription } from "@/components/ui/Alert";

import { MarkdownContainer } from "./MarkdownContainer";
import { Audio, File, Video } from "./outputs";

import type { SchemaProperty, ResponseData } from "@/types";
interface FlowResponseProps {
  responseSchema?: SchemaProperty | null;
  responseData?: ResponseData;
}

interface ResponsePropertyProps {
  name: string;
  property: SchemaProperty;
  value: ResponseData;
}

function ResponseProperty({ name, property, value }: ResponsePropertyProps) {
  const renderValue = () => {
    // Handle different qtype_type values
    switch (property.qtype_type) {
      case "text":
        return <MarkdownContainer>{String(value)}</MarkdownContainer>;

      case "boolean":
        return (
          <div className="bg-gray-50 dark:bg-gray-900 p-3 rounded">
            <p className="text-gray-800 dark:text-gray-200">{String(value)}</p>
          </div>
        );

      case "number":
      case "int":
      case "float":
        return (
          <div className="bg-gray-50 dark:bg-gray-900 p-3 rounded">
            <p className="text-gray-800 dark:text-gray-200 font-mono">
              {String(value)}
            </p>
          </div>
        );
      case "video": {
        const { mime, bytes_base64 } = JSON.parse(String(value));
        return <Video mime={mime} bytesBase64={bytes_base64} />;
      }
      case "audio": {
        const { mime, bytes_base64 } = JSON.parse(String(value));
        return <Audio mime={mime} bytesBase64={bytes_base64} />;
      }
      case "file": {
        const { mime, filename, bytes_base64 } = JSON.parse(String(value));
        return (
          <File fileName={filename} mime={mime} bytesBase64={bytes_base64} />
        );
      }
      default:
        <Alert variant="destructive">
          <AlertDescription>
            Unsupported response type:{" "}
            <code className="font-mono text-sm">
              {property.qtype_type || property.type}
            </code>
          </AlertDescription>
        </Alert>;
    }
  };

  return (
    <div className="space-y-2">
      {/* Property Label */}
      <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
        {property.title || name}
      </label>

      {/* Property Description */}
      {property.description && (
        <p className="text-xs text-gray-500 dark:text-gray-400">
          {property.description}
        </p>
      )}

      {/* Property Value */}
      {renderValue()}
    </div>
  );
}

export default function FlowResponse({
  responseSchema,
  responseData,
}: FlowResponseProps) {
  if (!responseData) {
    return (
      <div className="text-gray-500 dark:text-gray-400 text-sm">
        No response data to display
      </div>
    );
  }

  if (!responseSchema?.properties) {
    return (
      <div className="bg-gray-50 dark:bg-gray-900 p-4 rounded">
        <pre className="text-xs text-gray-800 dark:text-gray-200 overflow-x-auto whitespace-pre-wrap">
          {JSON.stringify(responseData, null, 2)}
        </pre>
      </div>
    );
  }

  // Extract outputs if the response follows the pattern: { outputs: { ... } }
  const outputsData =
    responseData && typeof responseData === "object"
      ? (responseData as Record<string, ResponseData>).outputs || responseData
      : responseData || {};

  return (
    <div className="space-y-4">
      {responseSchema.properties &&
        Object.entries(responseSchema.properties).map(
          ([propertyName, propertySchema]) => {
            const value = (outputsData as Record<string, ResponseData>)[
              propertyName
            ];

            if (value === undefined || value === null) {
              return null;
            }

            return (
              <ResponseProperty
                key={propertyName}
                name={propertyName}
                property={propertySchema}
                value={value}
              />
            );
          },
        )}
    </div>
  );
}
