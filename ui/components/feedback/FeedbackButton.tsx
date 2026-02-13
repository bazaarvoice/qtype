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

import type { FeedbackData, FeedbackSubmission } from "@/types/Feedback";
import type { FeedbackConfig } from "@/types/FlowMetadata";

interface FeedbackButtonProps {
  feedbackConfig: FeedbackConfig;
  spanId: string;
  traceId: string;
}

export function FeedbackButton({
  feedbackConfig,
  spanId,
  traceId,
}: FeedbackButtonProps) {
  const [submitted, setSubmitted] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showExplanation, setShowExplanation] = useState(false);
  const [pendingFeedback, setPendingFeedback] = useState<FeedbackData | null>(
    null,
  );

  if (submitted) {
    return (
      <div className="flex items-center gap-2 text-sm text-muted-foreground">
        <Check className="h-4 w-4 text-primary" />
        <span>Feedback submitted</span>
      </div>
    );
  }

  if (isSubmitting) {
    return (
      <div className="flex items-center gap-2 text-sm text-muted-foreground">
        <Loader2 className="h-4 w-4 animate-spin" />
        <span>Submitting...</span>
      </div>
    );
  }

  const handleFeedbackSubmit = async (
    feedback: FeedbackData,
    explanation?: string,
  ) => {
    setIsSubmitting(true);
    setError(null);

    try {
      const feedbackWithExplanation: FeedbackData = explanation
        ? { ...feedback, explanation }
        : feedback;

      const submission: FeedbackSubmission = {
        span_id: spanId,
        trace_id: traceId,
        feedback: feedbackWithExplanation,
      };

      await apiClient.submitFeedback(submission);

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

  const handleFeedbackClick = (feedback: FeedbackData) => {
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

      {error && <div className="text-sm text-destructive">{error}</div>}

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
