/**
 * RatingFeedback Component
 *
 * Star rating feedback widget (1-5 or 1-10 scale)
 */

"use client";

import { Star } from "lucide-react";
import { useState } from "react";

import { Button } from "@/components/ui/Button";

interface RatingFeedbackProps {
  scale: 5 | 10;
  onFeedback: (feedback: { type: "rating"; score: number }) => void;
}

export function RatingFeedback({ scale, onFeedback }: RatingFeedbackProps) {
  const [hoveredRating, setHoveredRating] = useState<number | null>(null);

  return (
    <div className="flex items-center gap-1">
      {Array.from({ length: scale }, (_, i) => i + 1).map((rating) => {
        const isFilled = hoveredRating ? rating <= hoveredRating : false;

        return (
          <Button
            key={rating}
            variant="ghost"
            size="sm"
            onClick={() => onFeedback({ type: "rating", score: rating })}
            onMouseEnter={() => setHoveredRating(rating)}
            onMouseLeave={() => setHoveredRating(null)}
            className="h-8 w-8 p-0 hover:bg-transparent"
            title={`Rate ${rating} out of ${scale}`}
          >
            <Star
              className={`h-4 w-4 ${
                isFilled ? "fill-yellow-400 text-yellow-400" : "text-gray-300"
              }`}
            />
          </Button>
        );
      })}
      <span className="ml-2 text-sm text-gray-500">
        {hoveredRating ? `${hoveredRating}/${scale}` : `Rate 1-${scale}`}
      </span>
    </div>
  );
}
