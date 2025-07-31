/**
 * Flow Input Component
 * 
 * Individual input field for a flow parameter
 */

'use client'

import TextInput from './inputs/text-input'

interface FlowInputProps {
  name: string
  property: {
    type: string
    title?: string
    description?: string
    [key: string]: any
  }
  required: boolean
  value?: any
  onChange?: (name: string, value: any) => void
}

export default function FlowInput({ 
  name, 
  property, 
  required, 
  value, 
  onChange 
}: FlowInputProps) {
  
  // Render the appropriate input component based on type
  const renderInput = () => {
    switch (property.type) {
      case 'text':
      case 'string':
        return (
          <TextInput
            name={name}
            property={property}
            required={required}
            value={value}
            onChange={onChange}
          />
        )
      
      // Placeholder cases for other types - will implement these next
      case 'boolean':
        return (
          <div className="bg-gray-50 dark:bg-gray-900 p-3 rounded border">
            <p className="text-xs text-gray-600 dark:text-gray-400">
              Boolean input coming soon...
            </p>
          </div>
        )
      
      case 'number':
      case 'int':
      case 'float':
        return (
          <div className="bg-gray-50 dark:bg-gray-900 p-3 rounded border">
            <p className="text-xs text-gray-600 dark:text-gray-400">
              Number input coming soon...
            </p>
          </div>
        )
      
      case 'date':
      case 'datetime':
      case 'time':
        return (
          <div className="bg-gray-50 dark:bg-gray-900 p-3 rounded border">
            <p className="text-xs text-gray-600 dark:text-gray-400">
              Date/time input coming soon...
            </p>
          </div>
        )
      
      case 'bytes':
      case 'file':
      case 'image':
      case 'audio':
      case 'video':
        return (
          <div className="bg-gray-50 dark:bg-gray-900 p-3 rounded border">
            <p className="text-xs text-gray-600 dark:text-gray-400">
              File upload input coming soon...
            </p>
          </div>
        )
      
      default:
        return (
          <div className="bg-gray-50 dark:bg-gray-900 p-3 rounded border">
            <p className="text-xs text-gray-600 dark:text-gray-400">
              Unknown input type: <code>{property.type}</code>
            </p>
          </div>
        )
    }
  }

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
  )
}
