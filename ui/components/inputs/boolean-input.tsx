/**
 * Boolean Input Component
 * 
 * Handles boolean input fields for flows using shadcn Switch
 */

'use client'

import { Switch } from '@/components/ui/switch'

interface BooleanInputProps {
  name: string
  property: {
    type: string
    title?: string
    description?: string
    [key: string]: any
  }
  required: boolean
  value?: boolean
  onChange?: (name: string, value: boolean) => void
}

export default function BooleanInput({ 
  name, 
  property, 
  required, 
  value = false, 
  onChange 
}: BooleanInputProps) {
  const handleChange = (checked: boolean) => {
    onChange?.(name, checked)
  }

  return (
    <div className="flex items-center space-x-3">
      <Switch
        checked={value}
        onCheckedChange={handleChange}
        required={required}
      />
      <div className="flex-1">
        <div className="text-sm text-gray-600 dark:text-gray-400">
          {value ? 'Enabled' : 'Disabled'}
        </div>
      </div>
    </div>
  )
}
