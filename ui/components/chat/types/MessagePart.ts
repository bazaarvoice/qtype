import type { MessagePartWithTextContent } from "../constants";

interface MessagePartWithText extends BaseMessagePart {
  type: MessagePartWithTextContent;
  text: string;
}

interface BaseMessagePart {
  type: string;
}

type MessagePart = MessagePartWithText | BaseMessagePart;

export type { MessagePart, MessagePartWithText };
