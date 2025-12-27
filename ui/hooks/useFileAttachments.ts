import { useState, useCallback, useRef } from "react";

import type { FileAttachment } from "@/types";

interface UseFileAttachmentsResult {
  files: FileAttachment[];
  fileError: string | null;
  handleFileSelect: (e: React.ChangeEvent<HTMLInputElement>) => Promise<void>;
  removeFile: (index: number) => void;
  clearFiles: () => void;
  reset: () => void;
  fileInputRef: React.RefObject<HTMLInputElement | null>;
}

const convertFileToDataUrl = (file: File): Promise<string> => {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve(reader.result as string);
    reader.onerror = () => reject(new Error("File read error"));
    reader.readAsDataURL(file);
  });
};

export function useFileAttachments(): UseFileAttachmentsResult {
  const [files, setFiles] = useState<FileAttachment[]>([]);
  const [fileError, setFileError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFileSelect = useCallback(
    async (e: React.ChangeEvent<HTMLInputElement>) => {
      const inputFiles = e.target.files;
      if (!inputFiles) return;
      setFileError(null);
      try {
        const newFiles: FileAttachment[] = await Promise.all(
          Array.from(inputFiles).map(async (file): Promise<FileAttachment> => {
            const url = await convertFileToDataUrl(file);
            return {
              type: "file",
              mediaType: file.type || "application/octet-stream",
              filename: file.name,
              url,
              size: file.size,
            };
          }),
        );
        setFiles((prev) => [...prev, ...newFiles]);
      } catch (err: unknown) {
        const errorMessage =
          err instanceof Error ? err.message : "Unknown error";
        setFileError(`Failed to process files: ${errorMessage}`);
      }
    },
    [],
  );

  const removeFile = useCallback((index: number) => {
    setFiles((prev) => prev.filter((_, i) => i !== index));
  }, []);

  const clearFiles = useCallback(() => {
    setFiles([]);
    if (fileInputRef.current) fileInputRef.current.value = "";
  }, []);

  const reset = useCallback(() => {
    clearFiles();
    setFileError(null);
  }, [clearFiles]);

  return {
    files,
    fileError,
    handleFileSelect,
    removeFile,
    clearFiles,
    reset,
    fileInputRef,
  };
}
