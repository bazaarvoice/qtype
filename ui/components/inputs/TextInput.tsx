/**
 * Text Input Component
 *
 * Handles text/string input fields for flows
 */

"use client";

import { Input } from "@/components/ui/Input";

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
  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    onChange?.(name, e.target.value);
  };

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
