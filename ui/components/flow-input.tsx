/**
 * Flow Input Component
 * 
 * Individual input field for a flow parameter
 */

'use client'

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
      
      {/* Placeholder Input */}
      <div className="bg-gray-50 dark:bg-gray-900 p-3 rounded border">
        <p className="text-xs text-gray-600 dark:text-gray-400">
          Input field for <code>{name}</code> ({property.type})
          {required ? ' (required)' : ' (optional)'}
        </p>
        
        {/* Show property details for development */}
        <details className="mt-2">
          <summary className="text-xs text-gray-500 cursor-pointer">Property Details</summary>
          <pre className="text-xs text-gray-400 mt-1 overflow-x-auto">
            {JSON.stringify(property, null, 2)}
          </pre>
        </details>
      </div>
    </div>
  )
}
