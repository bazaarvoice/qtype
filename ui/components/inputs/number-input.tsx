/**
 * Number Input Component
 * 
 * Handles number/int/float input fields for flows
 */

'use client'

import { Input } from '@/components/ui/input'

interface NumberInputProps {
  name: string
  property: {
    type: string
    title?: string
    description?: string
    minimum?: number
    maximum?: number
    [key: string]: any
  }
  required: boolean
  value?: number
  onChange?: (name: string, value: number) => void
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
    if (property.type === 'int') {
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
  const step = property.type === 'int' ? 1 : 'any'
  
  return (
    <Input
      type="number"
      placeholder={property.description || `Enter ${property.title || name}`}
      value={value || ''}
      onChange={handleChange}
      required={required}
      step={step}
      min={property.minimum}
      max={property.maximum}
      className="w-full"
    />
  )
}
