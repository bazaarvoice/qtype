/**
 * React hooks for API data fetching using SWR
 * 
 * These hooks provide a clean interface for fetching data from the FastAPI backend
 * with automatic caching, revalidation, and error handling.
 */

'use client'

import useSWR from 'swr'
import { apiClient, fetchOpenApiSpec, checkApiHealth, OpenAPISpec, ApiClientError } from '../apiClient'
export function useOpenApiSpec() {
  const { data, error, isLoading, mutate } = useSWR<OpenAPISpec, ApiClientError>(
    '/openapi.json',
    fetchOpenApiSpec,
    {
      // Revalidate every 5 minutes in case the API spec changes
      refreshInterval: 5 * 60 * 1000,
      // Don't revalidate on window focus for specs (they change infrequently)
      revalidateOnFocus: false,
      // Retry failed requests up to 3 times
      errorRetryCount: 3,
      // Use exponential backoff for retries
      errorRetryInterval: 5000,
    }
  )

  return {
    spec: data,
    isLoading,
    error,
    refresh: mutate,
  }
}

/**
 * Hook for checking API health status
 * 
 * @param enablePolling - Whether to continuously poll the health endpoint
 * @returns SWR response with health data, loading state, and error
 */
export function useApiHealth(enablePolling: boolean = false) {
  const { data, error, isLoading, mutate } = useSWR<
    { status: string; timestamp: string },
    ApiClientError
  >(
    '/health',
    checkApiHealth,
    {
      // Poll every 30 seconds if polling is enabled
      refreshInterval: enablePolling ? 30 * 1000 : 0,
      // Revalidate on focus to check if API came back online
      revalidateOnFocus: true,
      // Retry failed requests more aggressively for health checks
      errorRetryCount: 5,
      errorRetryInterval: 2000,
    }
  )

  return {
    health: data,
    isHealthy: data?.status === 'healthy',
    isLoading,
    error,
    refresh: mutate,
  }
}

/**
 * Hook for getting the current API base URL
 * This is useful for debugging or displaying connection info
 */
export function useApiConfig() {
  return {
    baseUrl: apiClient.getBaseUrl(),
    isDevelopment: process.env.NODE_ENV === 'development',
  }
}

/**
 * Custom fetcher function that can be used with SWR for other endpoints
 * 
 * @param endpoint - The API endpoint to fetch
 * @returns Promise with the fetched data
 */
export const apiFetcher = async <T>(endpoint: string): Promise<T> => {
  if (endpoint.startsWith('/openapi.json')) {
    return apiClient.getOpenApiSpec() as T
  }
  
  // For future endpoints, you can add more cases here
  throw new Error(`Unknown endpoint: ${endpoint}`)
}

/**
 * Generic hook for fetching data from any API endpoint
 * 
 * @param endpoint - The API endpoint to fetch from
 * @param options - SWR configuration options
 * @returns SWR response with data, loading state, and error
 */
export function useApiData<T>(
  endpoint: string | null,
  options?: {
    refreshInterval?: number
    revalidateOnFocus?: boolean
    errorRetryCount?: number
    errorRetryInterval?: number
  }
) {
  const { data, error, isLoading, mutate } = useSWR<T, ApiClientError>(
    endpoint,
    endpoint ? () => apiFetcher<T>(endpoint) : null,
    {
      refreshInterval: 0,
      revalidateOnFocus: true,
      errorRetryCount: 3,
      errorRetryInterval: 5000,
      ...options,
    }
  )

  return {
    data,
    isLoading,
    error,
    refresh: mutate,
  }
}
