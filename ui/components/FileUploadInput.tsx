"use client";

import { useCallback, useState, useRef } from "react";
import { useDropzone } from "react-dropzone";

import type { SchemaProperty, FlowInputValue } from "@/types";

interface FileUploadInputProps {
  name: string;
  property: SchemaProperty;
  required: boolean;
  value?: FlowInputValue;
  onChange?: (name: string, value: FlowInputValue) => void;
}

const BINARY_TYPES = new Set(["bytes", "file", "image", "audio", "video"]);

export default function FileUploadInput({
  name,
  property,
  required,
  value,
  onChange,
}: FileUploadInputProps) {
  const [filePreview, setFilePreview] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isReading, setIsReading] = useState(false);
  const [fileMeta, setFileMeta] = useState<{
    name: string;
    size: number;
    type: string;
  } | null>(null);

  const acceptMap: Record<string, Record<string, string[]>> = {
    image: { "image/*": [] },
    video: { "video/*": [] },
    audio: { "audio/*": [] },
    file: { "*/*": [] },
    bytes: { "*/*": [] },
  };
  const typeKey = property.qtype_type || "file";
  const accept = acceptMap[typeKey] ?? { "*/*": [] };

  const arrayBufferToBase64 = (buffer: ArrayBuffer): string => {
    // Chunk to avoid call stack overflow on large files
    const bytes = new Uint8Array(buffer);
    const chunkSize = 0x8000;
    let binary = "";
    for (let i = 0; i < bytes.length; i += chunkSize) {
      const chunk = bytes.subarray(i, i + chunkSize);
      binary += String.fromCharCode(...chunk);
    }
    return btoa(binary);
  };

  const humanSize = (bytes: number): string => {
    if (bytes < 1024) return `${bytes} B`;
    const kb = bytes / 1024;
    if (kb < 1024) return `${kb.toFixed(1)} KB`;
    const mb = kb / 1024;
    if (mb < 1024) return `${mb.toFixed(1)} MB`;
    const gb = mb / 1024;
    return `${gb.toFixed(1)} GB`;
  };

  const videoRef = useRef<HTMLVideoElement | null>(null);

  const handleDrop = useCallback(
    async (files: File[]) => {
      setError(null);
      const file = files[0];
      if (!file) return;
      setFileMeta({
        name: file.name,
        size: file.size,
        type: file.type || "application/octet-stream",
      });

      if (property.maxLength && file.size > property.maxLength) {
        setError(
          `File exceeds max size (${property.maxLength} bytes). Got ${file.size}.`,
        );
        return;
      }

      // Preview for image/video only
      if (file.type.startsWith("image/") || file.type.startsWith("video/")) {
        setFilePreview(URL.createObjectURL(file));
      } else {
        setFilePreview(null);
      }

      if (BINARY_TYPES.has(typeKey)) {
        try {
          setIsReading(true);
          const buffer = await file.arrayBuffer();
          // Send base64 string (Pydantic will decode to bytes)
          const base64 = arrayBufferToBase64(buffer);
          const output = JSON.stringify({
            filename: file.name,
            mime: file.type || "application/octet-stream",
            bytes_base64: base64,
          });
          onChange?.(name, output);
        } catch (e) {
          setError(
            e instanceof Error
              ? `Failed to read file: ${e.message}`
              : "Failed to read file",
          );
        } finally {
          setIsReading(false);
        }
      } else {
        // Fallback: pass File (should not happen for configured binary types)
        onChange?.(name, file as unknown as FlowInputValue);
      }
    },
    [name, onChange, property.maxLength, typeKey],
  );

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop: handleDrop,
    multiple: false,
    accept,
  });

  const renderSelectedInfo = () => {
    if (!value) return null;
    if (typeof value === "string" && BINARY_TYPES.has(typeKey)) {
      return (
        <p className="mt-2 text-xs text-gray-700 dark:text-gray-300">
          Bytes (base64) length: {value.length}
        </p>
      );
    }
    return null;
  };

  return (
    <div className="space-y-2">
      <div
        {...getRootProps()}
        className={`flex flex-col items-center justify-center rounded border border-dashed p-4 text-center cursor-pointer transition ${
          isDragActive
            ? "border-blue-500 bg-blue-50 dark:border-blue-400 dark:bg-blue-950"
            : "border-gray-300 dark:border-gray-600 bg-gray-50 dark:bg-gray-900"
        }`}
      >
        <input {...getInputProps()} aria-required={required} />
        <p className="text-xs text-gray-600 dark:text-gray-400">
          {isDragActive
            ? "Drop file here..."
            : `Drag & drop or click to select a ${typeKey} file`}
        </p>
        {isReading && (
          <p className="mt-2 text-xs text-blue-600 dark:text-blue-400">
            Reading file...
          </p>
        )}
        {renderSelectedInfo()}
      </div>

      {filePreview && fileMeta && (
        <div className="group relative w-full max-w-sm overflow-hidden rounded-lg border bg-black/5 dark:bg-white/5 shadow-sm">
          <div className="aspect-video w-full bg-black/30 flex items-center justify-center overflow-hidden">
            {typeKey === "image" && (
              <img
                src={filePreview}
                alt={fileMeta.name}
                className="h-full w-full object-cover transition group-hover:scale-[1.02]"
              />
            )}
            {typeKey === "video" && (
              <video
                ref={videoRef}
                src={filePreview}
                className="h-full w-full object-cover"
                muted
                playsInline
                preload="metadata"
              />
            )}
            {typeKey !== "image" && typeKey !== "video" && (
              <div className="text-xs text-gray-300">
                {fileMeta.type.split("/")[0].toUpperCase()}
              </div>
            )}
            <div className="pointer-events-none absolute inset-0 bg-gradient-to-b from-transparent via-black/30 to-black/70" />
          </div>
          <div className="absolute top-2 right-2 flex gap-1 opacity-0 group-hover:opacity-100 transition">
            <button
              type="button"
              onClick={() => {
                if (filePreview) URL.revokeObjectURL(filePreview);
                setFilePreview(null);
                setFileMeta(null);
                onChange?.(name, null);
              }}
              className="rounded bg-black/60 px-2 py-1 text-[10px] font-medium text-white hover:bg-black/80"
            >
              Remove
            </button>
            {typeKey === "video" && (
              <button
                type="button"
                onClick={() => videoRef.current?.play()}
                className="rounded bg-black/60 px-2 py-1 text-[10px] font-medium text-white hover:bg-black/80"
              >
                Play
              </button>
            )}
          </div>
          <div className="absolute bottom-0 left-0 right-0 px-3 py-2 flex flex-col gap-0.5">
            <div className="flex items-center justify-between">
              <span className="truncate text-[11px] font-medium text-white">
                {fileMeta.name}
              </span>
              <span className="text-[10px] text-gray-200">
                {humanSize(fileMeta.size)}
              </span>
            </div>
            <div className="flex items-center gap-2">
              <span className="rounded bg-white/15 px-1.5 py-0.5 text-[10px] text-gray-100 backdrop-blur">
                {typeKey}
              </span>
              <span className="truncate text-[10px] text-gray-300">
                {fileMeta.type}
              </span>
            </div>
          </div>
        </div>
      )}

      {error && (
        <p className="text-xs text-red-600 dark:text-red-400">{error}</p>
      )}
    </div>
  );
}
