import { Bot, User } from "lucide-react";
import { useMemo } from "react";

import { Avatar, AvatarFallback } from "@/components/ui/Avatar";

import FileDisplay from "./FileDisplay";
import ThinkingPanel from "./ThinkingPanel";

import type { FileAttachment } from "@/types";

interface MessagePart {
  type: string;
  text?: string;
}

interface MessageMetadata {
  statusMessage?: string;
  step_id?: string | number;
  [key: string]: unknown;
}

interface Message {
  role: string;
  content?: string;
  parts?: (MessagePart | FileAttachment)[];
  files?: FileAttachment[];
  experimental_attachments?: FileAttachment[];
  metadata?: MessageMetadata;
}

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
    // Only show status while streaming
    if (!isStreaming) return null;

    // Check metadata for status message first
    if (message.metadata?.statusMessage) {
      return message.metadata.statusMessage;
    }

    // Fallback to parsing parts for tool/step events
    let status = "Processing...";
    let reasoningContent = "";

    for (const part of catchAll) {
      switch (part.type) {
        case "step-start":
          status = "Starting ... ";
          break;

        case "finish-step":
          status = "Step completed";
          break;

        case "reasoning-start":
          status = "Thinking...";
          reasoningContent = "";
          break;

        case "reasoning-delta":
          if ("delta" in part) {
            reasoningContent += part.delta;
            status = `Thinking... ${reasoningContent}`;
          }
          break;

        case "reasoning-end":
          status = "Finished thinking";
          break;

        default:
          // Handle tool events (type starts with "tool-")
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

        {/* Show final text content - always appears in same position */}
        {textContent && (
          <div
            className={`rounded-lg px-3 py-2 text-sm whitespace-pre-wrap break-words ${
              isUser ? "bg-primary text-primary-foreground" : "bg-muted"
            }`}
          >
            {reasoningContent && (
              <ThinkingPanel reasoningContent={reasoningContent} />
            )}
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
