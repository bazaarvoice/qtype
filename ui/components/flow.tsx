/**
 * Flow Component
 * 
 * Interactive interface for executing a single flow
 */

'use client'

import { type FlowInfo } from '@/lib/api-client'
import FlowInputs from './flow-inputs'

interface FlowProps {
  flow: FlowInfo
}

export default function Flow({ flow }: FlowProps) {
  return (
    <div className="space-y-6">
      {/* Flow Header */}
      <div className="border-b pb-4">
        <h3 className="text-xl font-semibold text-gray-900 dark:text-white">
          {flow.name}
        </h3>
        <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
          {flow.path} • {flow.method.toUpperCase()}
        </p>
        {flow.description && (
          <p className="text-gray-600 dark:text-gray-300 mt-2">
            {flow.description}
          </p>
        )}
      </div>

    {/* Flow Inputs */}
    <FlowInputs 
        requestSchema={flow.requestSchema}
        onInputChange={(inputs) => {
        // TODO: Handle input changes
        console.log('Flow inputs changed:', inputs)
        }}
    />
    
    {/* Execute Button - Coming Soon */}
    <div className="mt-6 pt-4 border-t">
        <button 
        className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 transition-colors disabled:opacity-50"
        disabled
        >
        Execute Flow (Coming Soon)
        </button>
    </div>

      {/* Response Section */}
      <div className="bg-white dark:bg-gray-800 p-6 rounded-lg border">
        <h4 className="text-lg font-medium text-gray-900 dark:text-white mb-4">
          Response
        </h4>
        
        <div className="text-gray-500 dark:text-gray-400 text-sm">
          Response will appear here after execution...
        </div>
        
        {/* Show response schema info for now */}
        {flow.responseSchema && (
          <div className="mt-4 bg-gray-50 dark:bg-gray-900 p-4 rounded">
            <h5 className="font-medium text-gray-900 dark:text-white mb-2">Expected Response Schema</h5>
            <pre className="text-xs text-gray-600 dark:text-gray-400 overflow-x-auto">
              {JSON.stringify(flow.responseSchema, null, 2)}
            </pre>
          </div>
        )}
      </div>
    </div>
  )
}
