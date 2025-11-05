import { useEffect, useState } from "react";

type VideoValue =
  | string // raw base64 (no data: prefix)
  | {
      bytes_base64: string;
      mime_type?: string;
      filename?: string;
    };

interface VideoProps {
  value: VideoValue;
  className?: string;
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

function Video({ value, className }: VideoProps) {
  const [src, setSrc] = useState<string | null>(null);

  useEffect(() => {
    if (!value) {
      setSrc(null);
      return;
    }

    const base64 = typeof value === "string" ? value : value.bytes_base64;
    const mime = (typeof value === "object" && value.mime_type) || "video/mp4";

    if (!base64) {
      setSrc(null);
      return;
    }

    const blob = base64ToBlob(base64, mime);
    const url = URL.createObjectURL(blob);
    setSrc(url);

    return () => {
      URL.revokeObjectURL(url);
    };
  }, [value]);

  if (!src) {
    return (
      <div className="text-xs text-gray-500 dark:text-gray-400">
        No video data
      </div>
    );
  }

  return <video className={className} controls src={src} preload="metadata" />;
}

export { Video };
