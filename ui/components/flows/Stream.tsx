'use client'

import { useState, useCallback } from 'react'
import { type FlowInfo, apiClient, ApiClientError } from '@/lib/apiClient'
import FlowInputs from '../FlowInputs'
import { Button } from '@/components/ui/Button'
import { Alert, AlertDescription } from '@/components/ui/Alert'
import { useCompletion } from '@ai-sdk/react'
import { ScrollArea } from '@radix-ui/react-scroll-area'

import { MarkdownContainer } from '../MarkdownContainer'

import type { FlowInputValues } from '@/types/Flow'

function StreamFlow({ path, name, description, requestSchema }: FlowInfo) {
  const [inputs, setInputs] = useState<FlowInputValues>({})
  const [error, setError] = useState<string | null>(null)

  const streamingEndpoint = `${apiClient.getBaseUrl().replace(/\/$/, '')}${path}`

  const {
    completion,
    complete,
    isLoading,
    error: streamError,
  } = useCompletion({
    api: streamingEndpoint,
  })

  const handleInputChange = (newInputs: FlowInputValues) => {
    setInputs(newInputs)
  }

  const extractQuestion = useCallback((): string => {
    if ('question' in inputs) return String(inputs.question ?? '')
    const keys = Object.keys(inputs)

    if (keys.length === 1) return String(inputs[keys[0]] ?? '')
    return ''
  }, [inputs])

  const executeFlow = async () => {
    setError(null)
    const question = extractQuestion().trim()
    if (!question) {
      setError("Provide a 'question' input (or a single input field).")
      return
    }
    try {
      await complete(question)
    } catch (e) {
      const msg =
        e instanceof ApiClientError
          ? e.message
          : e instanceof Error
          ? e.message
          : 'Streaming failed'
      setError(msg)
    }
  }

  return (
    <div className="space-y-6">
      <div className="border-b pb-4">
        <h3 className="text-xl font-semibold text-gray-900 dark:text-white">
          {name}
        </h3>
        <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
          {streamingEndpoint} • POST (stream)
        </p>
        {description && (
          <p className="text-gray-600 dark:text-gray-300 mt-2">
            {description}
          </p>
        )}
      </div>

      <FlowInputs
        requestSchema={requestSchema || null}
        onInputChange={handleInputChange}
      />

      <div>
        {(error || streamError) && (
          <Alert variant="destructive" className="mb-4">
            <AlertDescription className="whitespace-pre-line">
              {(error || streamError?.message) ?? 'Error'}
            </AlertDescription>
          </Alert>
        )}
        {completion && (
        <ScrollArea className="flex-1 min-h-0">
        <MarkdownContainer>
            {completion}
        </MarkdownContainer>
        </ScrollArea>
        )}
      </div>

      <div className="mt-6 pt-4 border-t flex gap-2">
        <Button
          disabled={isLoading}
          onClick={executeFlow}
        >
          {isLoading ? 'Streaming...' : 'Execute Flow'}
        </Button>
      </div>
    </div>
  )
}

export { StreamFlow }