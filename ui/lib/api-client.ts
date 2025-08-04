/**
 * API Client for FastAPI Backend
 * 
 * Handles communication with the FastAPI server.
 * - In development: connects to http://localhost:8000
 * - In production: uses relative paths (./) for sub-mounted APIs
 */

import type { OpenAPIV3_1 } from 'openapi-types'
import { extractRequestSchema, extractResponseSchema } from './utils'
import type { SchemaProperty, FlowInputValues, ResponseData } from '../types/flow'

// Use the official OpenAPI spec type
export type OpenAPISpec = OpenAPIV3_1.Document

export interface ApiError {
  message: string;
  status: number;
  detail?: unknown;
}

/**
 * Custom error class for API-related errors
 */
export class ApiClientError extends Error {
  public status: number;
  public detail?: unknown;

  constructor(message: string, status: number, detail?: unknown) {
    super(message);
    this.name = 'ApiClientError';
    this.status = status;
    this.detail = detail;
  }
}

/**
 * Configuration for the API client
 */
interface ApiClientConfig {
  baseUrl: string;
  timeout?: number;
}

/**
 * Determines the appropriate base URL based on the environment
 */
function getBaseUrl(): string {
  // Use NEXT_PUBLIC_QTYPE_HOST environment variable if set, otherwise use relative path
  return process.env.NEXT_PUBLIC_QTYPE_HOST || '../';
}

/**
 * API Client class for managing communication with the FastAPI backend
 */
export class ApiClient {
  private config: ApiClientConfig;

  constructor(config?: Partial<ApiClientConfig>) {
    this.config = {
      baseUrl: getBaseUrl(),
      timeout: 10000, // 10 seconds default timeout
      ...config,
    };
  }

  /**
   * Generic fetch wrapper with error handling and timeout
   */
  private async fetchWithTimeout(
    url: string,
    options: RequestInit = {}
  ): Promise<Response> {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), this.config.timeout);

    try {
      const response = await fetch(url, {
        ...options,
        signal: controller.signal,
        headers: {
          'Content-Type': 'application/json',
          ...options.headers,
        },
      });

      clearTimeout(timeoutId);

      if (!response.ok) {
        let errorDetail;
        try {
          errorDetail = await response.json();
        } catch {
          errorDetail = { message: response.statusText };
        }

        // Create a more detailed error message
        let errorMessage = `API request failed: ${response.status} ${response.statusText}`;
        if (errorDetail?.detail) {
          // Handle detail as either string or object
          const detailString = typeof errorDetail.detail === 'string' 
            ? errorDetail.detail 
            : JSON.stringify(errorDetail.detail, null, 2);
          errorMessage += `\n${detailString}`;
        }
        throw new ApiClientError(
          errorMessage,
          response.status,
          errorDetail
        );
      }

      return response;
    } catch (error) {
      clearTimeout(timeoutId);
      
      if (error instanceof ApiClientError) {
        throw error;
      }

      if (error instanceof Error && error.name === 'AbortError') {
        throw new ApiClientError('Request timeout', 408);
      }

      throw new ApiClientError(
        `Network error: ${error instanceof Error ? error.message : 'Unknown error'}`,
        0
      );
    }
  }

  /**
   * Constructs the full URL for an endpoint
   */
  private getUrl(endpoint: string): string {
    const baseUrl = this.config.baseUrl.endsWith('/') 
      ? this.config.baseUrl.slice(0, -1) 
      : this.config.baseUrl;
    const cleanEndpoint = endpoint.startsWith('/') ? endpoint : `/${endpoint}`;
    
    return `${baseUrl}${cleanEndpoint}`;
  }

  /**
   * GET request helper
   */
  private async get<T>(endpoint: string): Promise<T> {
    const response = await this.fetchWithTimeout(this.getUrl(endpoint), {
      method: 'GET',
    });

    return response.json();
  }

  /**
   * POST request helper
   */
  private async post<T>(endpoint: string, data?: FlowInputValues): Promise<T> {
    const response = await this.fetchWithTimeout(this.getUrl(endpoint), {
      method: 'POST',
      body: data ? JSON.stringify(data) : undefined,
    });

    return response.json();
  }

  /**
   * Execute a flow with the given inputs
   */
  async executeFlow<T = ResponseData>(path: string, inputs?: FlowInputValues): Promise<T> {
    return this.post<T>(path, inputs);
  }

  /**
   * Fetches the OpenAPI specification from the API
   */
  async getOpenApiSpec(): Promise<OpenAPISpec> {
    return this.get<OpenAPISpec>('/openapi.json');
  }

  /**
   * Health check method to verify API connectivity
   */
  async healthCheck(): Promise<{ status: string; timestamp: string }> {
    try {
      // Try to fetch the OpenAPI spec as a basic health check
      await this.getOpenApiSpec();
      return {
        status: 'healthy',
        timestamp: new Date().toISOString(),
      };
    } catch (error) {
      throw new ApiClientError(
        `Health check failed: ${error instanceof Error ? error.message : 'Unknown error'}`,
        500,
        error
      );
    }
  }

  /**
   * Get the current base URL
   */
  getBaseUrl(): string {
    return this.config.baseUrl;
  }

  /**
   * Update the base URL (useful for testing or dynamic configuration)
   */
  setBaseUrl(baseUrl: string): void {
    this.config.baseUrl = baseUrl;
  }
}

/**
 * Default API client instance
 */
export const apiClient = new ApiClient();

/**
 * Hook-friendly function for use in React components
 * Returns a promise that can be used with SWR or React Query
 */
export const fetchOpenApiSpec = () => apiClient.getOpenApiSpec();

/**
 * Utility function to check if the API is available
 */
export const checkApiHealth = () => apiClient.healthCheck();

// =============================================================================
// OpenAPI Flow Processing
// =============================================================================

/**
 * Flow interface for extracted flow information
 */
export interface FlowInfo {
  id: string;
  name: string;
  path: string;
  method: string;
  mode: 'Complete' | 'Chat';
  description?: string;
  operationId?: string;
  tags: string[];
  requestSchema: SchemaProperty | null;
  responseSchema: SchemaProperty | null;
}

/**
 * Extracts flow information from OpenAPI specification
 * Returns flows with raw names (e.g., "simple_qa_flow") - use UI utilities to format for display
 */
export function extractFlowsFromSpec(spec: OpenAPISpec): FlowInfo[] {
  if (!spec?.paths) return []

  const flows: FlowInfo[] = []

  Object.entries(spec.paths).forEach(([path, pathData]: [string, OpenAPIV3_1.PathItemObject | undefined]) => {
    if (!pathData) return
    
    // Check each HTTP method in the path item
    const methods = ['get', 'post', 'put', 'delete', 'patch', 'head', 'options', 'trace'] as const
    
    methods.forEach((method) => {
      const methodData = pathData[method] as OpenAPIV3_1.OperationObject | undefined
      if (!methodData) return
      
      // Check if this is a flow endpoint (has 'flow' tag or path starts with /flows/)
      const isFlow =
        path.startsWith('/flows/') ||
        methodData.tags?.includes('flow')

      if (isFlow) {
        // Determine flow mode based on path pattern
        const isChatFlow = path.endsWith('/chat')
        const mode: 'Complete' | 'Chat' = isChatFlow ? 'Chat' : 'Complete'
        
        // Extract raw flow name from path
        const pathSegments = path.split('/')
        let rawFlowName: string
        
        if (isChatFlow) {
          // For chat flows like /flows/simple_qa_flow/chat, get the flow name
          rawFlowName = pathSegments[pathSegments.length - 2]
        } else {
          // For complete flows like /flows/simple_qa_flow, get the flow name
          rawFlowName = pathSegments[pathSegments.length - 1]
        }
        
        const flowId = `${method}-${path.replace(/[^a-zA-Z0-9]/g, '_')}`

        // Extract request schema
        const requestSchema = extractRequestSchema(methodData, spec)
        
        // Extract response schema (200 response)
        const responseSchema = extractResponseSchema(methodData, spec)

        flows.push({
          id: flowId,
          name: formatFlowNameForDisplay(rawFlowName), // Format name for display
          path,
          method,
          mode,
          description: methodData.description || methodData.summary,
          operationId: methodData.operationId,
          tags: methodData.tags || [],
          requestSchema,
          responseSchema
        })
      }
    })
  })

  return flows
}

/**
 * Formats a raw flow name for UI display
 * Converts snake_case to Title Case
 */
function formatFlowNameForDisplay(rawFlowName: string): string {
  return rawFlowName
    .split('_')
    .map((word: string) => word.charAt(0).toUpperCase() + word.slice(1))
    .join(' ')
}
