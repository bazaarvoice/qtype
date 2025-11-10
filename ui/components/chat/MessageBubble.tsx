import { Bot, User } from "lucide-react";

import { Avatar, AvatarFallback } from "@/components/ui/Avatar";

import { MarkdownContainer } from "../MarkdownContainer";

import { MessagePartWithTextContent } from "./constants";
import { deriveStatusFromParts } from "./utils/deriveStatusFromParts";

import { FileDisplay, ThinkingPanel } from ".";

import type { Message } from "./types";
import type { MessagePartWithText } from "./types/MessagePart";
import type { FileAttachment } from "@/types";

interface MessageBubbleProps {
  message: Message;
  isStreaming?: boolean;
}

interface StreamingPart {
  type: string;
  [key: string]: unknown;
}

function MessageBubble({ message, isStreaming = false }: MessageBubbleProps) {
  const isUser = message.role === "user";

  const reasoningContent = getPartContent(
    message,
    MessagePartWithTextContent.Reasoning,
  );
  const textContent = getPartContent(message, MessagePartWithTextContent.Text);

  const fileAttachments: FileAttachment[] =
    message.files ||
    message.experimental_attachments ||
    (message.parts?.filter((p): p is FileAttachment => p.type === "file") ??
      []);

  const excludedPartTypes = new Set(["text", "file"]);
  const statusParts = (message.parts ?? []).filter(
    (p) => !excludedPartTypes.has(p.type),
  ) as StreamingPart[];

  const statusMessage = deriveStatusFromParts(
    statusParts,
    message.metadata,
    isStreaming,
  );

  return (
    <div
      className={`flex gap-3 w-full ${
        isUser ? "justify-end" : "justify-start"
      }`}
    >
      {!isUser && (
        <Avatar className="h-8 w-8 flex-shrink-0">
          <AvatarFallback>
            <Bot className="h-4 w-4" />
          </AvatarFallback>
        </Avatar>
      )}

      <div className="flex-1 max-w-[75%] space-y-2">
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
          <MarkdownContainer chatBubble theme={isUser ? "dark" : "light"}>
            {textContent}
          </MarkdownContainer>
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

function getPartContent(
  { content, parts }: Message,
  partType: MessagePartWithTextContent,
): string {
  if (!parts?.length) {
    return content || "";
  }
  const matching = parts.filter(
    (p) => p.type === partType,
  ) as MessagePartWithText[];
  if (matching.length === 0 && content) {
    return content;
  }
  return matching.map((p) => p.text).join("");
}

export { MessageBubble };
