"use client";
import { useEffect, useState } from "react";

interface FileCardProps {
  mime: string;
  bytesBase64: string;
  fileName: string;
}
function FileCard({ mime, fileName, bytesBase64 }: FileCardProps) {
  const [url, setUrl] = useState<string | null>(null);

  useEffect(() => {
    try {
      const binary = atob(bytesBase64);
      const len = binary.length;
      const bytes = new Uint8Array(len);
      for (let i = 0; i < len; i += 1) {
        bytes[i] = binary.charCodeAt(i);
      }
      const blob = new Blob([bytes], { type: mime });
      const objectUrl = URL.createObjectURL(blob);
      setUrl(objectUrl);
      return () => URL.revokeObjectURL(objectUrl);
    } catch {
      setUrl(null);
    }
  }, [mime, bytesBase64]);

  const renderPreview = () => {
    if (!url) {
      return (
        <div className="p-4 text-sm text-gray-500 dark:text-gray-400">
          Unable to preview file.
        </div>
      );
    }
    if (mime.startsWith("image/")) {
      return (
        <img
          src={url}
          alt={fileName}
          className="h-48 w-full object-cover"
          loading="lazy"
        />
      );
    }
    if (mime.startsWith("video/")) {
      return (
        <video
          src={url}
          controls
          className="h-48 w-full bg-black object-contain"
        />
      );
    }
    if (mime === "application/pdf") {
      return (
        <iframe
          title={fileName}
          src={url}
          className="h-48 w-full"
          loading="lazy"
        />
      );
    }
    if (mime.startsWith("text/")) {
      return (
        <iframe
          title={fileName}
          src={url}
          className="h-48 w-full"
          loading="lazy"
        />
      );
    }
    return (
      <div className="flex h-48 w-full items-center justify-center text-xs text-gray-500 dark:text-gray-400">
        No inline preview for {mime}
      </div>
    );
  };

  return (
    <div className="group relative flex w-full max-w-sm flex-col overflow-hidden rounded-lg border border-gray-200 bg-white shadow-sm dark:border-gray-700 dark:bg-gray-900">
      {renderPreview()}
      <div className="flex items-center justify-between gap-2 px-3 py-2">
        <span className="truncate text-xs font-medium text-gray-700 dark:text-gray-300">
          {fileName}
        </span>
        {url && (
          <a
            href={url}
            download={fileName}
            className="rounded bg-blue-600 px-2 py-1 text-xs font-semibold text-white hover:bg-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-400"
            aria-label={`Download ${fileName}`}
          >
            Download
          </a>
        )}
      </div>
    </div>
  );
}

export { FileCard as File };
