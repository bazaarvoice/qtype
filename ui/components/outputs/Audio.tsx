"use client";

import { useEffect, useState } from "react";
interface AudioProps {
  mime: string;
  bytesBase64: string;
}

function base64ToBlob(b64: string, mime: string): Blob {
  const binary = atob(b64);
  const len = binary.length;
  const bytes = new Uint8Array(len);
  for (let i = 0; i < len; i++) {
    bytes[i] = binary.charCodeAt(i);
  }
  return new Blob([bytes], { type: mime });
}

function Audio({ mime, bytesBase64 }: AudioProps) {
  const [src, setSrc] = useState<string | null>(null);

  useEffect(() => {
    if (!bytesBase64) {
      setSrc(null);
      return;
    }

    try {
      const blob = base64ToBlob(bytesBase64, mime);
      const url = URL.createObjectURL(blob);
      setSrc(url);
      return () => {
        URL.revokeObjectURL(url);
      };
    } catch {
      setSrc(null);
    }
  }, [bytesBase64]);

  if (!src) {
    return (
      <div className="text-xs text-gray-500 dark:text-gray-400">
        No audio data
      </div>
    );
  }

  return (
    <div>
      <audio controls src={src} preload="metadata" />
    </div>
  );
}

export { Audio };
