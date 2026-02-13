/**
 * Types for feedback submission
 */

export interface ThumbsFeedbackData {
  type: "thumbs";
  value: boolean;
  explanation?: string;
}

export interface RatingFeedbackData {
  type: "rating";
  score: number;
  explanation?: string;
}

export interface CategoryFeedbackData {
  type: "category";
  categories: string[];
  explanation?: string;
}

export type FeedbackData =
  | ThumbsFeedbackData
  | RatingFeedbackData
  | CategoryFeedbackData;

export interface FeedbackSubmission {
  span_id: string;
  trace_id: string;
  feedback: FeedbackData;
}

export interface FeedbackResponse {
  status: "success";
  message: string;
}
