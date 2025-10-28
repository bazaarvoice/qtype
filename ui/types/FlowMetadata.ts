/**
 * Flow metadata from the /flows endpoint
 */
export interface FlowEndpoints {
  rest: string;
  stream?: string | null;
}

export interface FlowMetadata {
  id: string;
  description: string | null;
  interface_type: "Complete" | "Conversational" | null;
  session_inputs: string[];
  endpoints: FlowEndpoints;
  input_schema: Record<string, unknown>;
  output_schema: Record<string, unknown>;
}
