/**
 * FeedbackButton Component
 *
 * Displays feedback UI based on flow configuration and handles submission to Phoenix
 */

"use client";

import { Check, Loader2 } from "lucide-react";
import { useState } from "react";

import { apiClient } from "@/lib/apiClient";

import { CategoryFeedback } from "./CategoryFeedback";
import { FeedbackExplanationModal } from "./FeedbackExplanationModal";
import { RatingFeedback } from "./RatingFeedback";
import { ThumbsFeedback } from "./ThumbsFeedback";

import type { FeedbackConfig } from "@/types/FlowMetadata";

interface FeedbackButtonProps {
  feedbackConfig: FeedbackConfig;
  spanId: string;
  traceId: string;
  telemetryEnabled: boolean;
}

export function FeedbackButton({
  feedbackConfig,
  spanId,
  traceId,
  telemetryEnabled,
}: FeedbackButtonProps) {
  const [submitted, setSubmitted] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showExplanation, setShowExplanation] = useState(false);
  const [pendingFeedback, setPendingFeedback] = useState<{
    type: "thumbs" | "rating" | "category";
    value?: boolean;
    score?: number;
    categories?: string[];
  } | null>(null);

  if (!telemetryEnabled) {
    return null; // Don't show feedback if telemetry is not enabled
  }

  if (submitted) {
    return (
      <div className="flex items-center gap-2 text-sm text-green-600">
        <Check className="h-4 w-4" />
        <span>Feedback submitted</span>
      </div>
    );
  }

  if (isSubmitting) {
    return (
      <div className="flex items-center gap-2 text-sm text-gray-500">
        <Loader2 className="h-4 w-4 animate-spin" />
        <span>Submitting...</span>
      </div>
    );
  }

  const handleFeedbackSubmit = async (
    feedback: {
      type: "thumbs" | "rating" | "category";
      value?: boolean;
      score?: number;
      categories?: string[];
    },
    explanation?: string,
  ) => {
    setIsSubmitting(true);
    setError(null);

    try {
      // Construct feedback data based on type
      let feedbackData:
        | { type: "thumbs"; value: boolean; explanation?: string }
        | { type: "rating"; score: number; explanation?: string }
        | { type: "category"; categories: string[]; explanation?: string };

      if (feedback.type === "thumbs" && feedback.value !== undefined) {
        feedbackData = { type: "thumbs", value: feedback.value, explanation };
      } else if (feedback.type === "rating" && feedback.score !== undefined) {
        feedbackData = { type: "rating", score: feedback.score, explanation };
      } else if (feedback.type === "category" && feedback.categories) {
        feedbackData = {
          type: "category",
          categories: feedback.categories,
          explanation,
        };
      } else {
        throw new Error("Invalid feedback data");
      }

      await apiClient.submitFeedback({
        span_id: spanId,
        trace_id: traceId,
        feedback: feedbackData,
      });

      setSubmitted(true);
      setPendingFeedback(null);
      setShowExplanation(false);
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Failed to submit feedback",
      );
      setPendingFeedback(null);
      setShowExplanation(false);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleFeedbackClick = (feedback: {
    type: "thumbs" | "rating" | "category";
    value?: boolean;
    score?: number;
    categories?: string[];
  }) => {
    // If explanation is enabled, show modal first
    if (feedbackConfig.explanation) {
      setPendingFeedback(feedback);
      setShowExplanation(true);
    } else {
      // Submit directly without explanation
      handleFeedbackSubmit(feedback);
    }
  };

  return (
    <div className="flex flex-col gap-2">
      <div className="flex items-center gap-2">
        {feedbackConfig.type === "thumbs" && (
          <ThumbsFeedback onFeedback={handleFeedbackClick} />
        )}
        {feedbackConfig.type === "rating" && (
          <RatingFeedback
            scale={feedbackConfig.scale}
            onFeedback={handleFeedbackClick}
          />
        )}
        {feedbackConfig.type === "category" && (
          <CategoryFeedback
            categories={feedbackConfig.categories}
            allowMultiple={feedbackConfig.allow_multiple}
            onFeedback={handleFeedbackClick}
          />
        )}
      </div>

      {error && <div className="text-sm text-red-600">{error}</div>}

      {showExplanation && pendingFeedback && (
        <FeedbackExplanationModal
          isOpen={showExplanation}
          onClose={() => {
            setShowExplanation(false);
            setPendingFeedback(null);
          }}
          onSubmit={(explanation) => {
            handleFeedbackSubmit(pendingFeedback, explanation);
          }}
        />
      )}
    </div>
  );
}
