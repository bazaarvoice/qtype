/**
 * Flow Inputs Component
 *
 * Container for all input components based on the flow's request schema
 */

"use client";

import { useState } from "react";

import FlowInput from "./FlowInput";

import type { SchemaProperty, FlowInputValues, FlowInputValue } from "@/types";

interface FlowInputsProps {
  requestSchema: SchemaProperty | null;
  onInputChange?: (inputs: FlowInputValues) => void;
}

export default function FlowInputs({
  requestSchema,
  onInputChange,
}: FlowInputsProps) {
  const [inputValues, setInputValues] = useState<FlowInputValues>({});

  if (!requestSchema) {
    return (
      <div className="text-gray-500 dark:text-gray-400 text-sm">
        No input parameters required for this flow.
      </div>
    );
  }

  // Extract properties and required fields from schema
  const properties = requestSchema.properties || {};
  const requiredFields = requestSchema.required || [];

  // Handle individual input changes
  const handleInputChange = (name: string, value: FlowInputValue) => {
    const newValues = { ...inputValues, [name]: value };
    setInputValues(newValues);
    onInputChange?.(newValues);
  };

  // If no properties, show no inputs message
  if (Object.keys(properties).length === 0) {
    return (
      <div className="text-gray-500 dark:text-gray-400 text-sm">
        No input parameters defined for this flow.
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <h5 className="font-medium text-gray-900 dark:text-white">Inputs</h5>

      {/* Render input for each property */}
      <div className="space-y-4">
        {Object.entries(properties).map(([name, property]) => (
          <FlowInput
            key={name}
            name={name}
            property={property as SchemaProperty}
            required={requiredFields.includes(name)}
            value={inputValues[name]}
            onChange={handleInputChange}
          />
        ))}
      </div>
    </div>
  );
}
