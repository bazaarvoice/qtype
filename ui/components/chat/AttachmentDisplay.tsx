import { Paperclip, X } from "lucide-react";

import { Button } from "@/components/ui/Button";

import type { FileAttachment } from "@/types";

interface AttachmentDisplayProps {
  files: FileAttachment[];
  onRemoveFile: (index: number) => void;
  onClearAll: () => void;
}

const formatFileSize = (bytes: number) =>
  `${(bytes / (1024 * 1024)).toFixed(1)} MB`;

function AttachmentDisplay({
  files,
  onRemoveFile,
  onClearAll,
}: AttachmentDisplayProps) {
  return (
    <div className="mb-3 p-2 bg-muted rounded">
      <div className="flex items-center justify-between mb-2">
        <span className="text-sm font-medium">
          Attachments ({files.length})
        </span>
        <Button
          type="button"
          variant="ghost"
          size="sm"
          onClick={onClearAll}
          className="h-6 px-2"
        >
          Clear all
        </Button>
      </div>
      <div className="space-y-1">
        {files.map((file, index) => (
          <div
            key={`${file.filename}-${index}`}
            className="flex items-center justify-between bg-background rounded p-2"
          >
            <div className="flex items-center gap-2 min-w-0">
              <Paperclip className="h-4 w-4 flex-shrink-0" />
              <span className="text-sm truncate">{file.filename}</span>
              <span className="text-xs text-muted-foreground">
                ({formatFileSize(file.size || 0)})
              </span>
            </div>
            <Button
              type="button"
              variant="ghost"
              size="sm"
              onClick={() => onRemoveFile(index)}
              className="h-6 w-6 p-0 flex-shrink-0"
              aria-label={`Remove ${file.filename}`}
            >
              <X className="h-3 w-3" />
            </Button>
          </div>
        ))}
      </div>
    </div>
  );
}

export { AttachmentDisplay };
