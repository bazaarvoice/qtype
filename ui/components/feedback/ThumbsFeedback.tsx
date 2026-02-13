/**
 * ThumbsFeedback Component
 *
 * Binary thumbs up/down feedback widget
 */

"use client";

import { ThumbsDown, ThumbsUp } from "lucide-react";

import { Button } from "@/components/ui/Button";

interface ThumbsFeedbackProps {
  onFeedback: (feedback: { type: "thumbs"; value: boolean }) => void;
}

export function ThumbsFeedback({ onFeedback }: ThumbsFeedbackProps) {
  return (
    <div className="flex items-center gap-1">
      <Button
        variant="outline"
        size="sm"
        onClick={() => onFeedback({ type: "thumbs", value: true })}
        className="h-8 w-8 p-0"
        title="Thumbs up"
      >
        <ThumbsUp className="h-4 w-4" />
      </Button>
      <Button
        variant="outline"
        size="sm"
        onClick={() => onFeedback({ type: "thumbs", value: false })}
        className="h-8 w-8 p-0"
        title="Thumbs down"
      >
        <ThumbsDown className="h-4 w-4" />
      </Button>
    </div>
  );
}
