"use client"

import * as React from "react"
import { Input } from "@/components/ui/input"

interface TimeInputProps {
  name: string
  property: {
    type: string
    format?: string
    title?: string
    description?: string
    [key: string]: any
  }
  required: boolean
  value?: string
  onChange?: (name: string, value: string) => void
}

export default function TimeInput({ name, property, value, onChange, required }: TimeInputProps) {
  const [timeValue, setTimeValue] = React.useState<string>(value || '')

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
