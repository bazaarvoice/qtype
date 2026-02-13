/**
 * Flow metadata from the /flows endpoint
 */
export interface FlowEndpoints {
  rest: string;
  stream?: string | null;
}

export interface ThumbsFeedbackConfig {
  type: "thumbs";
  explanation: boolean;
}

export interface RatingFeedbackConfig {
  type: "rating";
  scale: 5 | 10;
  explanation: boolean;
}

export interface CategoryFeedbackConfig {
  type: "category";
  categories: string[];
  allow_multiple: boolean;
  explanation: boolean;
}

export type FeedbackConfig =
  | ThumbsFeedbackConfig
  | RatingFeedbackConfig
  | CategoryFeedbackConfig;

export interface FlowMetadata {
  id: string;
  description: string | null;
  interface_type: "Complete" | "Conversational" | null;
  session_inputs: string[];
  endpoints: FlowEndpoints;
  input_schema: Record<string, unknown>;
  output_schema: Record<string, unknown>;
  feedback?: FeedbackConfig | null;
  telemetry_enabled: boolean;
}
