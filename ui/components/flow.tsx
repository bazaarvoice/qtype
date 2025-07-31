/**
 * Flow Component
 * 
 * Interactive interface for executing a single flow
 */

'use client'

import { useState } from 'react'
import { type FlowInfo, apiClient, ApiClientError } from '@/lib/api-client'
import FlowInputs from './flow-inputs'
import { Button } from '@/components/ui/button'
import { Alert, AlertDescription } from '@/components/ui/alert'

interface FlowProps {
  flow: FlowInfo
}

export default function Flow({ flow }: FlowProps) {
  const [inputs, setInputs] = useState<Record<string, any>>({})
  const [isExecuting, setIsExecuting] = useState(false)
  const [response, setResponse] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)

  const handleInputChange = (newInputs: Record<string, any>) => {
    setInputs(newInputs)
  }

  const executeFlow = async () => {
    setIsExecuting(true)
    setError(null)
    setResponse(null)

    try {
      const responseData = await apiClient.executeFlow(flow.path, inputs)
      setResponse(JSON.stringify(responseData, null, 2))
    } catch (err) {
      if (err instanceof ApiClientError) {
        // Use the formatted error message from ApiClientError
        setError(err.message)
      } else {
        setError(err instanceof Error ? err.message : 'An unknown error occurred')
      }
    } finally {
      setIsExecuting(false)
    }
  }
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
        onInputChange={handleInputChange}
    />
    
    {/* Execute Button */}
    <div className="mt-6 pt-4 border-t">
        <Button 
        disabled={isExecuting}
        onClick={executeFlow}
        >
        {isExecuting ? 'Executing...' : 'Execute Flow'}
        </Button>
    </div>

      {/* Response Section */}
      <div className="bg-white dark:bg-gray-800 p-6 rounded-lg border">
        <h4 className="text-lg font-medium text-gray-900 dark:text-white mb-4">
          Response
        </h4>
        
        {error && (
          <Alert variant="destructive" className="mb-4">
            <AlertDescription>
              <div className="whitespace-pre-line">
                <span className="font-medium">Error:</span>
                <br />
                {error}
              </div>
            </AlertDescription>
          </Alert>
        )}
        
        {response ? (
          <div className="bg-gray-50 dark:bg-gray-900 p-4 rounded">
            <pre className="text-xs text-gray-800 dark:text-gray-200 overflow-x-auto whitespace-pre-wrap">
              {response}
            </pre>
          </div>
        ) : (
          <div className="text-gray-500 dark:text-gray-400 text-sm">
            {isExecuting ? 'Executing request...' : 'Response will appear here after execution...'}
          </div>
        )}
        
        {/* {flow.responseSchema && (
          <div className="mt-4 bg-gray-50 dark:bg-gray-900 p-4 rounded">
            <h5 className="font-medium text-gray-900 dark:text-white mb-2">Expected Response Schema</h5>
            <pre className="text-xs text-gray-600 dark:text-gray-400 overflow-x-auto">
              {JSON.stringify(flow.responseSchema, null, 2)}
            </pre>
          </div>
        )} */}
      </div>
    </div>
  )
}
