/**
 * Flow Component
 * 
 * Interactive interface for executing a single flow
 */

'use client'

import { useState } from 'react'
import { type FlowInfo, apiClient, ApiClientError } from '@/lib/api-client'
import type { FlowInputValues, ResponseData } from '@/types/flow'
import FlowInputs from '../flow-inputs'
import FlowResponse from '../flow-response'
import { Button } from '@/components/ui/button'
import { Alert, AlertDescription } from '@/components/ui/alert'

interface FlowProps {
  flow: FlowInfo
}

function RestFlow({ flow }: FlowProps) {
  const [inputs, setInputs] = useState<FlowInputValues>({})
  const [isExecuting, setIsExecuting] = useState(false)
  const [responseData, setResponseData] = useState<ResponseData | null>(null)
  const [error, setError] = useState<string | null>(null)

  const handleInputChange = (newInputs: FlowInputValues) => {
    setInputs(newInputs)
  }

  const executeFlow = async () => {
    setIsExecuting(true)
    setError(null)
    setResponseData(null)

    try {
      const responseData = await apiClient.executeFlow(flow.path, inputs)
      setResponseData(responseData)
    } catch (err) {
      if (err instanceof ApiClientError) {
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

      <FlowInputs
        requestSchema={flow.requestSchema || null}
        onInputChange={handleInputChange}
      />

      <div>
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

        {responseData && (
          <FlowResponse
            responseSchema={flow.responseSchema?.properties?.outputs}
            responseData={responseData}
          />
        )}
      </div>

      <div className="mt-6 pt-4 border-t">
        <Button
          disabled={isExecuting}
          onClick={executeFlow}
        >
          {isExecuting ? 'Executing...' : 'Execute Flow'}
        </Button>
      </div>


    </div>
  )
}

export { RestFlow }
