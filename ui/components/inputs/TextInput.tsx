/**
 * Text Input Component
 *
 * Handles text/string input fields for flows
 */

"use client";

import { Input } from "@/components/ui/Input";
import { Textarea } from "@/components/ui/textarea";

import type { SchemaProperty, FlowInputValue } from "@/types";

interface TextInputProps {
  name: string;
  property: SchemaProperty;
  required: boolean;
  value?: FlowInputValue;
  onChange?: (name: string, value: FlowInputValue) => void;
}

export default function TextInput({
  name,
  property,
  required,
  value = "",
  onChange,
}: TextInputProps) {
  const handleChange = (
    e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>,
  ) => {
    onChange?.(name, e.target.value);
  };

  // Check for UI hints
  const uiConfig = (
    property as SchemaProperty & { "x-ui"?: { widget?: string; rows?: number } }
  )["x-ui"];
  const widget = uiConfig?.widget;

  // Render textarea if specified in UI config
  if (widget === "textarea") {
    return (
      <Textarea
        placeholder={property.description || `Enter ${property.title || name}`}
        value={String(value || "")}
        onChange={handleChange}
        required={required}
        className="w-full"
        rows={uiConfig?.rows || 5}
      />
    );
  }

  // Default to single-line input
  return (
    <Input
      type="text"
      placeholder={property.description || `Enter ${property.title || name}`}
      value={String(value || "")}
      onChange={handleChange}
      required={required}
      className="w-full"
    />
  );
}
