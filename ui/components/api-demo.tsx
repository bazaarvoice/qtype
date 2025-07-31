/**
 * API Demo Component
 * 
 * Demonstrates the usage of API hooks for connecting to the FastAPI backend
 */

'use client'

import { useOpenApiSpec, useApiHealth, useApiConfig } from '@/lib/hooks/use-api'

export default function ApiDemo() {
  const { spec, isLoading: specLoading, error: specError, refresh: refreshSpec } = useOpenApiSpec()
  const { health, isHealthy, isLoading: healthLoading, error: healthError, refresh: refreshHealth } = useApiHealth(true)
  const { baseUrl, isDevelopment } = useApiConfig()

  return (
    <div className="space-y-6 p-6 bg-gray-50 dark:bg-gray-900 rounded-lg">
      <div className="border-b pb-4">
        <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-2">
          FastAPI Connection Demo
        </h2>
        <p className="text-gray-600 dark:text-gray-400">
          Demonstrating connection to FastAPI backend at: 
          <code className="ml-2 px-2 py-1 bg-gray-200 dark:bg-gray-800 rounded text-sm">
            {baseUrl}
          </code>
        </p>
        <p className="text-sm text-gray-500 mt-1">
          Environment: {isDevelopment ? 'Development' : 'Production'}
        </p>
      </div>

      {/* API Health Status */}
      <div className="bg-white dark:bg-gray-800 p-4 rounded-md border">
        <div className="flex items-center justify-between mb-3">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
            API Health Status
          </h3>
          <button
            onClick={() => refreshHealth()}
            className="px-3 py-1 bg-blue-500 text-white rounded text-sm hover:bg-blue-600 transition-colors"
          >
            Refresh
          </button>
        </div>
        
        {healthLoading ? (
          <div className="flex items-center text-gray-600 dark:text-gray-400">
            <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-500 mr-2"></div>
            Checking API health...
          </div>
        ) : healthError ? (
          <div className="text-red-600 dark:text-red-400">
            <p className="font-medium">❌ API Unavailable</p>
            <p className="text-sm mt-1">Error: {healthError.message}</p>
            <p className="text-xs text-gray-500 mt-1">
              Make sure your FastAPI server is running on {baseUrl}
            </p>
          </div>
        ) : (
          <div className="text-green-600 dark:text-green-400">
            <p className="font-medium">✅ API Healthy</p>
            <p className="text-sm mt-1">Last checked: {health?.timestamp}</p>
          </div>
        )}
      </div>

      {/* OpenAPI Specification */}
      <div className="bg-white dark:bg-gray-800 p-4 rounded-md border">
        <div className="flex items-center justify-between mb-3">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
            OpenAPI Specification
          </h3>
          <button
            onClick={() => refreshSpec()}
            className="px-3 py-1 bg-blue-500 text-white rounded text-sm hover:bg-blue-600 transition-colors"
          >
            Refresh
          </button>
        </div>

        {specLoading ? (
          <div className="flex items-center text-gray-600 dark:text-gray-400">
            <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-500 mr-2"></div>
            Loading API specification...
          </div>
        ) : specError ? (
          <div className="text-red-600 dark:text-red-400">
            <p className="font-medium">❌ Failed to load API spec</p>
            <p className="text-sm mt-1">Error: {specError.message}</p>
          </div>
        ) : spec ? (
          <div className="space-y-3">
            <div className="text-green-600 dark:text-green-400">
              <p className="font-medium">✅ API Spec Loaded</p>
            </div>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
              <div>
                <p className="font-medium text-gray-700 dark:text-gray-300">API Title:</p>
                <p className="text-gray-600 dark:text-gray-400">{spec.info.title}</p>
              </div>
              <div>
                <p className="font-medium text-gray-700 dark:text-gray-300">Version:</p>
                <p className="text-gray-600 dark:text-gray-400">{spec.info.version}</p>
              </div>
              <div>
                <p className="font-medium text-gray-700 dark:text-gray-300">OpenAPI Version:</p>
                <p className="text-gray-600 dark:text-gray-400">{spec.openapi}</p>
              </div>
              <div>
                <p className="font-medium text-gray-700 dark:text-gray-300">Available Endpoints:</p>
                <p className="text-gray-600 dark:text-gray-400">
                  {Object.keys(spec.paths || {}).length} endpoints
                </p>
              </div>
            </div>

            {spec.info.description && (
              <div>
                <p className="font-medium text-gray-700 dark:text-gray-300">Description:</p>
                <p className="text-gray-600 dark:text-gray-400">{spec.info.description}</p>
              </div>
            )}

            {/* Show available endpoints */}
            {spec.paths && Object.keys(spec.paths).length > 0 && (
              <div>
                <p className="font-medium text-gray-700 dark:text-gray-300 mb-2">Available Endpoints:</p>
                <div className="bg-gray-100 dark:bg-gray-700 p-3 rounded text-xs font-mono max-h-32 overflow-y-auto">
                  {Object.keys(spec.paths).map((path) => (
                    <div key={path} className="text-gray-800 dark:text-gray-200">
                      {path}
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        ) : null}
      </div>

      {/* Connection Tips */}
      <div className="bg-blue-50 dark:bg-blue-900/20 p-4 rounded-md border border-blue-200 dark:border-blue-800">
        <h4 className="font-semibold text-blue-900 dark:text-blue-100 mb-2">
          💡 Connection Tips
        </h4>
        <ul className="text-sm text-blue-800 dark:text-blue-200 space-y-1">
          <li>• In development: Make sure your FastAPI server is running on port 8000</li>
          <li>• In production: The API should be mounted at the same path as this frontend</li>
          <li>• Health checks run automatically every 30 seconds</li>
          <li>• The API spec is cached and refreshed every 5 minutes</li>
        </ul>
      </div>
    </div>
  )
}
