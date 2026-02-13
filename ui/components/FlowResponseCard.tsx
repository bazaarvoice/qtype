/**
 * Flow Response Card Component
 *
 * Card view for a single flow response
 */

"use client";

import { FeedbackButton } from "@/components/feedback";
import { Alert, AlertDescription } from "@/components/ui/Alert";
import { getTelemetryIdsFromValue, METADATA_FIELD } from "@/lib/telemetry";

import { MarkdownContainer } from "./MarkdownContainer";
import {
  Audio,
  Bytes,
  CitationUrl,
  DateTime,
  File,
  Thinking,
  Video,
  Image,
} from "./outputs";

import type { SchemaProperty, ResponseData } from "@/types";
import type { FeedbackConfig } from "@/types/FlowMetadata";

interface ResponsePropertyProps {
  name: string;
  property: SchemaProperty;
  value: ResponseData;
}

function ResponseProperty({ name, property, value }: ResponsePropertyProps) {
  const renderValue = () => {
    switch (property.qtype_type) {
      case "text":
        return (
          <MarkdownContainer chatBubble>{String(value)}</MarkdownContainer>
        );

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
      case "image": {
        const { mime, filename, bytes_base64 } = JSON.parse(String(value));
        return (
          <Image mime={mime} fileName={filename} bytesBase64={bytes_base64} />
        );
      }
      case "audio": {
        const { mime, bytes_base64 } = JSON.parse(String(value));
        return <Audio mime={mime} bytesBase64={bytes_base64} />;
      }
      case "file":
      case "citation_document": {
        const { mime, filename, bytes_base64 } = JSON.parse(String(value));
        return (
          <File fileName={filename} mime={mime} bytesBase64={bytes_base64} />
        );
      }
      case "thinking": {
        return <Thinking reasoningContent={String(value)} />;
      }
      case "citation_url": {
        return <CitationUrl url={String(value)} />;
      }
      case "datetime": {
        return <DateTime value={String(value)} date time />;
      }
      case "date": {
        return <DateTime value={String(value)} date />;
      }
      case "time": {
        return <DateTime value={String(value)} time />;
      }
      case "bytes": {
        const { mime, filename, bytes_base64 } = JSON.parse(String(value));
        return (
          <Bytes fileName={filename} mime={mime} bytesBase64={bytes_base64} />
        );
      }
      default:
        return (
          <Alert variant="destructive">
            <AlertDescription>
              Unsupported response type:{" "}
              <code className="font-mono text-sm">
                {property.qtype_type || property.type}
              </code>
            </AlertDescription>
          </Alert>
        );
    }
  };

  return (
    <div className="space-y-2">
      <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
        {property.title || name}
      </label>

      {property.description && (
        <p className="text-xs text-gray-500 dark:text-gray-400">
          {property.description}
        </p>
      )}

      {renderValue()}
    </div>
  );
}

interface FlowResponseCardProps {
  responseSchema?: SchemaProperty | null;
  responseData?: ResponseData;
  feedbackConfig?: FeedbackConfig | null;
  telemetryEnabled?: boolean;
}

export default function FlowResponseCard({
  responseSchema,
  responseData,
  feedbackConfig,
  telemetryEnabled = false,
}: FlowResponseCardProps) {
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

  const outputsData =
    responseData && typeof responseData === "object"
      ? (responseData as Record<string, ResponseData>).outputs || responseData
      : responseData || {};

  const telemetryIds = getTelemetryIdsFromValue(responseData);

  return (
    <div className="space-y-4">
      {responseSchema.properties &&
        Object.entries(responseSchema.properties)
          .filter(([propertyName]) => propertyName !== METADATA_FIELD)
          .map(([propertyName, propertySchema]) => {
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
          })}

      {feedbackConfig && telemetryEnabled && telemetryIds && (
        <div className="pt-4 border-t">
          <FeedbackButton
            feedbackConfig={feedbackConfig}
            spanId={telemetryIds.spanId}
            traceId={telemetryIds.traceId}
          />
        </div>
      )}
    </div>
  );
}
