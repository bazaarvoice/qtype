"use client";

import { useEffect, useState } from "react";

// Supported audio value shapes: raw base64 string OR structured object
// bytes_base64 should NOT include a data: prefix; just the base64 payload
// mime_type is optional; defaults to audio/mpeg
export type AudioValue =
  | string
  | {
      bytes_base64: string;
      mime_type?: string;
      filename?: string;
    };

interface AudioProps {
  value: AudioValue | null | undefined;
  className?: string;
  autoPlay?: boolean;
  loop?: boolean;
  showMeta?: boolean; // display filename + size estimate
}

function base64ToBlob(b64: string, mime: string): Blob {
  // Convert base64 string into raw binary and wrap in Blob
  const binary = atob(b64);
  const len = binary.length;
  const bytes = new Uint8Array(len);
  for (let i = 0; i < len; i++) {
    bytes[i] = binary.charCodeAt(i);
  }
  return new Blob([bytes], { type: mime });
}

function estimateSizeFromBase64(b64: string): number {
  const padding = b64.endsWith("==") ? 2 : b64.endsWith("=") ? 1 : 0;
  return Math.floor((b64.length * 3) / 4) - padding;
}

function Audio({
  value,
  className,
  autoPlay = false,
  loop = false,
  showMeta = false,
}: AudioProps) {
  const [src, setSrc] = useState<string | null>(null);
  const [filename, setFilename] = useState<string | null>(null);
  const [sizeBytes, setSizeBytes] = useState<number | null>(null);

  useEffect(() => {
    if (!value) {
      setSrc(null);
      setFilename(null);
      setSizeBytes(null);
      return;
    }

    const base64 = typeof value === "string" ? value : value.bytes_base64;
    const mime = (typeof value === "object" && value.mime_type) || "audio/mpeg";
    const name =
      typeof value === "object" && value.filename ? value.filename : null;

    if (!base64) {
      setSrc(null);
      setFilename(null);
      setSizeBytes(null);
      return;
    }

    try {
      const blob = base64ToBlob(base64, mime);
      const url = URL.createObjectURL(blob);
      setSrc(url);
      setFilename(name);
      setSizeBytes(estimateSizeFromBase64(base64));
      return () => {
        URL.revokeObjectURL(url);
      };
    } catch {
      setSrc(null);
    }
  }, [value]);

  if (!src) {
    return (
      <div className="text-xs text-gray-500 dark:text-gray-400">
        No audio data
      </div>
    );
  }

  return (
    <div className={className}>
      <audio
        controls
        src={src}
        autoPlay={autoPlay}
        loop={loop}
        preload="metadata"
      />
      {showMeta && (
        <div className="mt-1 flex flex-wrap gap-2 text-[10px] text-gray-600 dark:text-gray-300">
          {filename && (
            <span className="truncate max-w-[150px]">{filename}</span>
          )}
          {sizeBytes !== null && (
            <span>{(sizeBytes / 1024).toFixed(1)} KB</span>
          )}
        </div>
      )}
    </div>
  );
}

export { Audio };
