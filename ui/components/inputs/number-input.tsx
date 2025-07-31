/**
 * Number Input Component
 * 
 * Handles numeric input fields for flows
 */

'use client'

import { Input } from '@/components/ui/input'
import type { SchemaProperty, FlowInputValue } from '../../types/flow'

interface NumberInputProps {
  name: string
  property: SchemaProperty
  required: boolean
  value?: FlowInputValue
  onChange?: (name: string, value: FlowInputValue) => void
}

export default function NumberInput({ 
  name, 
  property, 
  required, 
  value, 
  onChange 
}: NumberInputProps) {
  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const stringValue = e.target.value
    
    // Handle empty input
    if (stringValue === '') {
      onChange?.(name, 0)
      return
    }

    // Parse based on type
    let numericValue: number
    if (property.type === 'integer' || property.format === 'int32' || property.format === 'int64') {
      numericValue = parseInt(stringValue, 10)
    } else {
      numericValue = parseFloat(stringValue)
    }

    // Only call onChange if the value is valid
    if (!isNaN(numericValue)) {
      onChange?.(name, numericValue)
    }
  }

  // Determine step based on type
  const step = (property.type === 'integer' || property.format === 'int32' || property.format === 'int64') ? 1 : 'any'
  
  return (
    <Input
      type="number"
      placeholder={property.description || `Enter ${property.title || name}`}
      value={String(value || '')}
      onChange={handleChange}
      required={required}
      step={step}
      min={property.minimum}
      max={property.maximum}
      className="w-full"
    />
  )
}
