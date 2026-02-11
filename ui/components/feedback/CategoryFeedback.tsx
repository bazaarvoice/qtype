/**
 * CategoryFeedback Component
 *
 * Categorical feedback with predefined tags (single or multi-select)
 */

"use client";

import { Check } from "lucide-react";
import { useState } from "react";

import { Button } from "@/components/ui/Button";

interface CategoryFeedbackProps {
  categories: string[];
  allowMultiple: boolean;
  onFeedback: (feedback: { type: "category"; categories: string[] }) => void;
}

export function CategoryFeedback({
  categories,
  allowMultiple,
  onFeedback,
}: CategoryFeedbackProps) {
  const [selectedCategories, setSelectedCategories] = useState<Set<string>>(
    new Set(),
  );

  const handleCategoryClick = (category: string) => {
    if (allowMultiple) {
      // Multi-select mode
      const newSelected = new Set(selectedCategories);
      if (newSelected.has(category)) {
        newSelected.delete(category);
      } else {
        newSelected.add(category);
      }
      setSelectedCategories(newSelected);
    } else {
      // Single-select mode - submit immediately
      onFeedback({ type: "category", categories: [category] });
    }
  };

  const handleSubmit = () => {
    if (selectedCategories.size > 0) {
      onFeedback({
        type: "category",
        categories: Array.from(selectedCategories),
      });
    }
  };

  return (
    <div className="flex flex-wrap items-center gap-2">
      {categories.map((category) => {
        const isSelected = selectedCategories.has(category);
        return (
          <Button
            key={category}
            variant={isSelected ? "default" : "outline"}
            size="sm"
            onClick={() => handleCategoryClick(category)}
            className="h-8"
          >
            {isSelected && <Check className="mr-1 h-3 w-3" />}
            {category}
          </Button>
        );
      })}
      {allowMultiple && selectedCategories.size > 0 && (
        <Button variant="default" size="sm" onClick={handleSubmit}>
          Submit ({selectedCategories.size})
        </Button>
      )}
    </div>
  );
}
