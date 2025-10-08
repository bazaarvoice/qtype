"use client"

import * as React from "react"
import { Input } from "@/components/ui/Input"
import type { SchemaProperty, FlowInputValue } from '../../types/Flow'

interface TimeInputProps {
  name: string
  property: SchemaProperty
  required: boolean
  value?: FlowInputValue
  onChange?: (name: string, value: FlowInputValue) => void
}

export default function TimeInput({ name, property, value, onChange, required }: TimeInputProps) {
  const [timeValue, setTimeValue] = React.useState<string>(String(value || ''))

  const handleTimeChange = (time: string) => {
    setTimeValue(time)
    onChange?.(name, time)
  }

  return (
    <div className="space-y-2">
      <label className="text-sm font-medium">
        {property.title || 'Time'} {required && <span className="text-red-500">*</span>}
      </label>
      
      <Input
        type="time"
        value={timeValue}
        onChange={(e) => handleTimeChange(e.target.value)}
        step="1" // Include seconds
        className="w-full"
        placeholder="HH:MM:SS"
      />
      
      {property.description && (
        <p className="text-sm text-muted-foreground">{property.description}</p>
      )}
    </div>
  )
}
