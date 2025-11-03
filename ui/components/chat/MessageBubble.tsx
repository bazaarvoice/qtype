import { Bot, User } from "lucide-react";
import { useMemo } from "react";

import { Avatar, AvatarFallback } from "@/components/ui/Avatar";

import FileDisplay from "./FileDisplay";
import ThinkingPanel from "./ThinkingPanel";
import { deriveStatusFromParts } from "./utils/deriveStatusFromParts";

import type { Message } from "./types";
import type { FileAttachment } from "@/types";

interface MessageBubbleProps {
  message: Message;
  isStreaming?: boolean;
}

export default function MessageBubble({
  message,
  isStreaming = false,
}: MessageBubbleProps) {
  const isUser = message.role === "user";

  const textContent = useMemo(() => {
    return (
      message.content ||
      message.parts
        ?.filter((p) => p.type === "text")
        .map((p) => ("text" in p ? p.text : ""))
        .join("") ||
      ""
    );
  }, [message]);

  const reasoningContent = useMemo(() => {
    return (
      message.content ||
      message.parts
        ?.filter((p) => p.type === "reasoning")
        .map((p) => ("text" in p ? p.text : ""))
        .join("") ||
      ""
    );
  }, [message]);

  const fileAttachments = useMemo((): FileAttachment[] => {
    const files =
      message.files ||
      message.experimental_attachments ||
      message.parts?.filter((p): p is FileAttachment => p.type === "file") ||
      [];
    return files;
  }, [message]);

  const catchAll = useMemo(() => {
    const knownTypes = new Set(["text", "file"]);
    return message.parts?.filter((p) => !knownTypes.has(p.type)) || [];
  }, [message]);

  const statusMessage = useMemo(() => {
    const status = deriveStatusFromParts(
      catchAll,
      message.metadata,
      isStreaming,
    );
    return status;
  }, [catchAll, isStreaming, message.metadata]);

  return (
    <div
      className={`flex gap-3 w-full ${isUser ? "justify-end" : "justify-start"}`}
    >
      {!isUser && (
        <Avatar className="h-8 w-8 flex-shrink-0">
          <AvatarFallback>
            <Bot className="h-4 w-4" />
          </AvatarFallback>
        </Avatar>
      )}

      <div className="flex-1 max-w-[75%] space-y-2">
        {/* Fixed height status area - prevents layout jumping */}
        <div className="min-h-[1.5rem] flex items-center">
          {statusMessage && (
            <div className="text-xs italic text-muted-foreground bg-muted/30 px-2 py-1 rounded transition-all duration-200">
              {statusMessage}
              {message.metadata?.step_id && (
                <span className="opacity-70 ml-2">
                  (Step: {message.metadata.step_id})
                </span>
              )}
            </div>
          )}
        </div>

        {reasoningContent && (
          <ThinkingPanel reasoningContent={reasoningContent} />
        )}
        {textContent && (
          <div
            className={`rounded-lg px-3 py-2 text-sm whitespace-pre-wrap break-words ${
              isUser ? "bg-primary text-primary-foreground" : "bg-muted"
            }`}
          >
            {textContent}
          </div>
        )}

        {fileAttachments.map((file, index) => (
          <FileDisplay
            key={`${file.filename}-${index}`}
            mediaType={file.mediaType}
            filename={file.filename}
            url={file.url}
            size={file.size}
          />
        ))}
      </div>

      {isUser && (
        <Avatar className="h-8 w-8 flex-shrink-0">
          <AvatarFallback>
            <User className="h-4 w-4" />
          </AvatarFallback>
        </Avatar>
      )}
    </div>
  );
}
