/**
 * Text Input Component
 * 
 * Handles text/string input fields for flows
 */

'use client'

import { Input } from '@/components/ui/input'

interface TextInputProps {
  name: string
  property: {
    type: string
    title?: string
    description?: string
    [key: string]: any
  }
  required: boolean
  value?: string
  onChange?: (name: string, value: string) => void
}

export default function TextInput({ 
  name, 
  property, 
  required, 
  value = '', 
  onChange 
}: TextInputProps) {
  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    onChange?.(name, e.target.value)
  }

  return (
    <Input
      type="text"
      placeholder={property.description || `Enter ${property.title || name}`}
      value={value}
      onChange={handleChange}
      required={required}
      className="w-full"
    />
  )
}
