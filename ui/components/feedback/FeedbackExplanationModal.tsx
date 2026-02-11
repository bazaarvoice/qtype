/**
 * FeedbackExplanationModal Component
 *
 * Optional modal for adding text explanation to feedback
 */

"use client";

import { X } from "lucide-react";
import { useState } from "react";

import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";

interface FeedbackExplanationModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (explanation?: string) => void;
}

export function FeedbackExplanationModal({
  isOpen,
  onClose,
  onSubmit,
}: FeedbackExplanationModalProps) {
  const [explanation, setExplanation] = useState("");

  if (!isOpen) return null;

  const handleSubmit = () => {
    onSubmit(explanation.trim() || undefined);
  };

  const handleSkip = () => {
    onSubmit(undefined);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
      <Card className="w-full max-w-md p-6">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold">Add Explanation (Optional)</h3>
          <Button
            variant="ghost"
            size="sm"
            onClick={onClose}
            className="h-8 w-8 p-0"
          >
            <X className="h-4 w-4" />
          </Button>
        </div>

        <div className="space-y-4">
          <textarea
            value={explanation}
            onChange={(e) => setExplanation(e.target.value)}
            placeholder="Why did you give this feedback? (optional)"
            className="w-full min-h-[100px] p-3 border rounded-md resize-none focus:outline-none focus:ring-2 focus:ring-blue-500"
            autoFocus
          />

          <div className="flex justify-end gap-2">
            <Button variant="outline" onClick={handleSkip}>
              Skip
            </Button>
            <Button onClick={handleSubmit}>Submit</Button>
          </div>
        </div>
      </Card>
    </div>
  );
}
