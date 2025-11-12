/**
 * Streaming status derivation utility.
 * Centralizes logic for computing a human-readable status string
 * from arbitrary streaming parts and optional metadata.
 */

import type { StatusMetadata } from "../types";
import type { StreamingPart } from "../types/StreamingPart";

function deriveStatusFromParts(
  parts: StreamingPart[] | undefined,
  metadata: StatusMetadata | undefined,
  isStreaming: boolean,
): string | null {
  if (!isStreaming) return null;

  if (metadata?.statusMessage) return metadata.statusMessage;

  if (!parts || parts.length === 0) return "Processing...";

  let status = "Processing...";

  for (const part of parts) {
    switch (part.type) {
      case "step-start":
        status = "Starting ... ";
        break;
      case "finish-step":
        status = "Step completed";
        break;
      case "reasoning":
        status = "Thinking...";
        break;
      case "text":
        status = "Generating response...";
        break;
      default:
        if (part.type.startsWith("tool-")) {
          const toolName = part.type.replace("tool-", "");
          if ("state" in part) {
            switch (part.state) {
              case "input-available":
                status = `Calling ${toolName}...`;
                break;
              case "output-available":
                status = `Tool ${toolName} returned successfully`;
                break;
              default:
                status = `Using ${toolName}...`;
            }
          } else {
            status = `Using ${toolName}...`;
          }
        }
    }
  }

  return status;
}

export { deriveStatusFromParts };
