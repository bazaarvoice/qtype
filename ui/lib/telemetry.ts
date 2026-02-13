/**
 * Telemetry helpers.
 *
 * Centralizes extraction of telemetry IDs (span_id, trace_id) from metadata.
 */

export const METADATA_FIELD = "metadata";

export interface TelemetryIds {
  spanId: string;
  traceId: string;
}

type UnknownRecord = Record<string, unknown>;

function isRecord(value: unknown): value is UnknownRecord {
  return typeof value === "object" && value !== null;
}

export function getTelemetryIdsFromMetadata(
  metadata: unknown,
): TelemetryIds | null {
  if (!isRecord(metadata)) return null;

  const spanId = metadata.span_id;
  const traceId = metadata.trace_id;

  if (typeof spanId !== "string" || typeof traceId !== "string") {
    return null;
  }

  if (spanId.length === 0 || traceId.length === 0) {
    return null;
  }

  return { spanId, traceId };
}

export function getTelemetryIdsFromValue(value: unknown): TelemetryIds | null {
  if (!isRecord(value)) return null;

  return getTelemetryIdsFromMetadata(value[METADATA_FIELD]);
}
