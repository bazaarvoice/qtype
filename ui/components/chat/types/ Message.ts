import type { MessageMetadata } from "./MessageMetadata";
import type { MessagePart } from "./MessagePart";
import type { FileAttachment } from "@/types";

interface Message {
  role: string;
  content?: string;
  parts?: (MessagePart | FileAttachment)[];
  files?: FileAttachment[];
  experimental_attachments?: FileAttachment[];
  metadata?: MessageMetadata;
}

export type { Message };
