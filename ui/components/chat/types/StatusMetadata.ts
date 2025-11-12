interface StatusMetadata {
  statusMessage?: string;
  step_id?: string | number;
  [key: string]: unknown;
}

export type { StatusMetadata };
