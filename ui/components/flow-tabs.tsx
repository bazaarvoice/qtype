/**
 * Flow Tabs Component
 * 
 * Creates tabs for each flow endpoint found in the OpenAPI specification
 */

'use client'

import { useOpenApiSpec } from '@/lib/hooks/use-api'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'

export default function FlowTabs() {
  const { spec, isLoading, error } = useOpenApiSpec()

  // Extract flows from the OpenAPI spec
  const flows = extractFlowsFromSpec(spec)

  if (isLoading) {
    return (
      <div className="flex items-center justify-center p-8">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"></div>
        <span className="ml-2 text-gray-600 dark:text-gray-400">Loading flows...</span>
      </div>
    )
  }

  if (error) {
    return (
      <div className="p-6 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg">
        <p className="text-red-600 dark:text-red-400 font-medium">Failed to load flows</p>
        <p className="text-red-500 dark:text-red-300 text-sm mt-1">{error.message}</p>
      </div>
    )
  }

  if (!flows.length) {
    return (
      <div className="p-6 bg-gray-50 dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-lg">
        <p className="text-gray-600 dark:text-gray-400">No flows found in the API specification.</p>
      </div>
    )
  }

  return (
    <div className="w-full">
      <Tabs defaultValue={flows[0]?.id} className="w-full">
        <TabsList className="grid w-full" style={{ gridTemplateColumns: `repeat(${flows.length}, minmax(0, 1fr))` }}>
          {flows.map((flow) => (
            <TabsTrigger key={flow.id} value={flow.id} className="text-sm">
              {flow.name}
            </TabsTrigger>
          ))}
        </TabsList>
        
        {flows.map((flow) => (
          <TabsContent key={flow.id} value={flow.id} className="mt-6">
            <div className="space-y-4">
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

              {/* Placeholder content for now */}
              <div className="bg-gray-50 dark:bg-gray-900 p-6 rounded-lg border-2 border-dashed border-gray-200 dark:border-gray-700">
                <div className="text-center">
                  <h4 className="text-lg font-medium text-gray-900 dark:text-white mb-2">
                    Flow Interface Coming Soon
                  </h4>
                  <p className="text-gray-600 dark:text-gray-400 text-sm">
                    This tab will contain the interactive interface for the <code>{flow.name}</code> flow.
                  </p>
                  
                  {/* Show some flow details */}
                  <div className="mt-4 text-left bg-gray-100 dark:bg-gray-800 p-4 rounded text-xs">
                    <div className="font-mono space-y-1">
                      <div><span className="text-gray-500">Endpoint:</span> {flow.path}</div>
                      <div><span className="text-gray-500">Method:</span> {flow.method.toUpperCase()}</div>
                      <div><span className="text-gray-500">Operation ID:</span> {flow.operationId}</div>
                      {flow.tags.length > 0 && (
                        <div><span className="text-gray-500">Tags:</span> {flow.tags.join(', ')}</div>
                      )}
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </TabsContent>
        ))}
      </Tabs>
    </div>
  )
}

/**
 * Extracts flow information from OpenAPI specification
 */
function extractFlowsFromSpec(spec: any) {
  if (!spec?.paths) return []

  const flows: Array<{
    id: string
    name: string
    path: string
    method: string
    description?: string
    operationId?: string
    tags: string[]
  }> = []

  Object.entries(spec.paths).forEach(([path, pathData]: [string, any]) => {
    Object.entries(pathData).forEach(([method, methodData]: [string, any]) => {
      // Check if this is a flow endpoint (has 'flow' tag or path starts with /flows/)
      const isFlow = 
        path.startsWith('/flows/') || 
        methodData.tags?.includes('flow')

      if (isFlow) {
        const flowName = extractFlowName(path, methodData)
        const flowId = `${method}-${path.replace(/[^a-zA-Z0-9]/g, '_')}`

        flows.push({
          id: flowId,
          name: flowName,
          path,
          method,
          description: methodData.description || methodData.summary,
          operationId: methodData.operationId,
          tags: methodData.tags || []
        })
      }
    })
  })

  return flows
}

/**
 * Extracts a human-readable flow name from the path and operation data
 */
function extractFlowName(path: string, methodData: any): string {

  const pathSegments = path.split('/')
  const flowSegment = pathSegments[pathSegments.length - 1]
  
  // Convert snake_case to Title Case
  return flowSegment
    .split('_')
    .map((word: string) => word.charAt(0).toUpperCase() + word.slice(1))
    .join(' ')
}
