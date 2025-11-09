/**
 * Flow Input Component
 *
 * Individual input field for a flow parameter
 */

"use client";

import { Alert, AlertDescription } from "@/components/ui/Alert";

import BooleanInput from "./inputs/BooleanInput";
import DatePickerInput from "./inputs/DatePickerInput";
import DateTimeInput from "./inputs/DatetimeInput";
import FileUploadInput from "./inputs/FileUploadInput";
import NumberInput from "./inputs/NumberInput";
import TextInput from "./inputs/TextInput";
import TimeInput from "./inputs/TimeInput";

import type { SchemaProperty, FlowInputValue } from "@/types";

interface FlowInputProps {
  name: string;
  property: SchemaProperty;
  required: boolean;
  value?: FlowInputValue;
  onChange?: (name: string, value: FlowInputValue) => void;
}

export default function FlowInput({
  name,
  property,
  required,
  value,
  onChange,
}: FlowInputProps) {
  // Render the appropriate input component based on type
  const renderInput = () => {
    switch (property.qtype_type) {
      case "text":
      case "thinking":
      case "citation_url":
        return (
          <TextInput
            name={name}
            property={property}
            required={required}
            value={value}
            onChange={onChange}
          />
        );

      case "date":
        return (
          <DatePickerInput
            name={name}
            property={property}
            required={required}
            value={value}
            onChange={onChange}
          />
        );

      case "time":
        return (
          <TimeInput
            name={name}
            property={property}
            required={required}
            value={value}
            onChange={onChange}
          />
        );

      case "datetime":
        return (
          <DateTimeInput
            name={name}
            property={property}
            required={required}
            value={value}
            onChange={onChange}
          />
        );

      // Placeholder cases for other types - will implement these next
      case "boolean":
        return (
          <BooleanInput
            name={name}
            property={property}
            required={required}
            value={value}
            onChange={onChange}
          />
        );

      case "number":
      case "int":
      case "float":
        return (
          <NumberInput
            name={name}
            property={property}
            required={required}
            value={value}
            onChange={onChange}
          />
        );

      case "bytes":
      case "file":
      case "citation_document":
      case "image":
      case "audio":
      case "video":
        return (
          <FileUploadInput
            name={name}
            property={property}
            required={required}
            value={value}
            onChange={onChange}
          />
        );

      default:
        return (
          <Alert variant="destructive">
            <AlertDescription>
              Unknown input type:{" "}
              <code className="font-mono text-sm">{property.type}</code>
            </AlertDescription>
          </Alert>
        );
    }
  };

  return (
    <div className="space-y-2">
      {/* Input Label */}
      <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
        {property.title || name}
        {required && <span className="text-red-500 ml-1">*</span>}
      </label>

      {/* Input Description */}
      {property.description && (
        <p className="text-xs text-gray-500 dark:text-gray-400">
          {property.description}
        </p>
      )}

      {/* Input Component */}
      {renderInput()}
    </div>
  );
}
