interface FileAttachment {
  type: "file";
  mediaType: string;
  filename: string;
  url: string;
  size?: number;
}

export type { FileAttachment };
