import { useEffect, useState } from "react";
interface VideoProps {
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

function Video({ mime, bytesBase64 }: VideoProps) {
  const [src, setSrc] = useState<string | null>(null);

  useEffect(() => {
    if (!bytesBase64) {
      setSrc(null);
      return;
    }

    if (!bytesBase64) {
      setSrc(null);
      return;
    }

    const blob = base64ToBlob(bytesBase64, mime);
    const url = URL.createObjectURL(blob);
    setSrc(url);

    return () => {
      URL.revokeObjectURL(url);
    };
  }, [bytesBase64, mime]);

  if (!src) {
    return (
      <div className="text-xs text-gray-500 dark:text-gray-400">
        No video data
      </div>
    );
  }

  return <video controls src={src} preload="metadata" />;
}

export { Video };
