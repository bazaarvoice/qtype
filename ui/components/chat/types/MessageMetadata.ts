interface MessageMetadata {
  statusMessage?: string;
  step_id?: string | number;
  [key: string]: unknown;
}

export type { MessageMetadata };
