/**
 * API Client for FastAPI Backend
 *
 * Handles communication with the FastAPI server.
 * - In development: connects to http://localhost:8000
 * - In production: uses relative paths (./) for sub-mounted APIs
 */

import type { FlowMetadata } from "@/types";
import type { FlowInputValues, ResponseData } from "@/types";
import type { OpenAPIV3_1 } from "openapi-types";

// Use the official OpenAPI spec type
export type OpenAPISpec = OpenAPIV3_1.Document;

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
    this.name = "ApiClientError";
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
  return process.env.NEXT_PUBLIC_QTYPE_HOST || "../";
}

/**
 * API Client class for managing communication with the FastAPI backend
 */
export class ApiClient {
  private config: ApiClientConfig;

  constructor(config?: Partial<ApiClientConfig>) {
    this.config = {
      baseUrl: getBaseUrl(),
      timeout: 500000, // 500 seconds default timeout
      ...config,
    };
  }

  /**
   * Generic fetch wrapper with error handling and timeout
   */
  private async fetchWithTimeout(
    url: string,
    options: RequestInit = {},
  ): Promise<Response> {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), this.config.timeout);

    try {
      const response = await fetch(url, {
        ...options,
        signal: controller.signal,
        headers: {
          "Content-Type": "application/json",
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
          const detailString =
            typeof errorDetail.detail === "string"
              ? errorDetail.detail
              : JSON.stringify(errorDetail.detail, null, 2);
          errorMessage += `\n${detailString}`;
        }
        throw new ApiClientError(errorMessage, response.status, errorDetail);
      }

      return response;
    } catch (error) {
      clearTimeout(timeoutId);

      if (error instanceof ApiClientError) {
        throw error;
      }

      if (error instanceof Error && error.name === "AbortError") {
        throw new ApiClientError("Request timeout", 408);
      }

      throw new ApiClientError(
        `Network error: ${error instanceof Error ? error.message : "Unknown error"}`,
        0,
      );
    }
  }

  /**
   * Constructs the full URL for an endpoint
   */
  private getUrl(endpoint: string): string {
    const baseUrl = this.config.baseUrl.endsWith("/")
      ? this.config.baseUrl.slice(0, -1)
      : this.config.baseUrl;
    const cleanEndpoint = endpoint.startsWith("/") ? endpoint : `/${endpoint}`;

    return `${baseUrl}${cleanEndpoint}`;
  }

  /**
   * GET request helper
   */
  private async get<T>(endpoint: string): Promise<T> {
    const response = await this.fetchWithTimeout(this.getUrl(endpoint), {
      method: "GET",
    });

    return response.json();
  }

  /**
   * POST request helper
   */
  private async post<T>(
    endpoint: string,
    data?: FlowInputValues | Record<string, unknown>,
  ): Promise<T> {
    const response = await this.fetchWithTimeout(this.getUrl(endpoint), {
      method: "POST",
      body: data ? JSON.stringify(data) : undefined,
    });

    return response.json();
  }

  /**
   * Execute a flow with the given inputs
   */
  async executeFlow<T = ResponseData>(
    path: string,
    inputs?: FlowInputValues,
  ): Promise<T> {
    return this.post<T>(path, inputs);
  }

  /**
   * Fetches the OpenAPI specification from the API
   */
  async getOpenApiSpec(): Promise<OpenAPISpec> {
    return this.get<OpenAPISpec>("/openapi.json");
  }

  /**
   * Fetches flow metadata from the /flows endpoint
   */
  async getFlows(): Promise<FlowMetadata[]> {
    return this.get<FlowMetadata[]>("/flows");
  }

  /**
   * Health check method to verify API connectivity
   */
  async healthCheck(): Promise<{ status: string; timestamp: string }> {
    try {
      // Try to fetch the flows metadata as a basic health check
      await this.getFlows();
      return {
        status: "healthy",
        timestamp: new Date().toISOString(),
      };
    } catch (error) {
      throw new ApiClientError(
        `Health check failed: ${error instanceof Error ? error.message : "Unknown error"}`,
        500,
        error,
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

  /**
   * Submit user feedback on a flow output
   */
  async submitFeedback(feedback: {
    span_id: string;
    trace_id: string;
    feedback:
      | { type: "thumbs"; value: boolean; explanation?: string }
      | { type: "rating"; score: number; explanation?: string }
      | { type: "category"; categories: string[]; explanation?: string };
  }): Promise<{ status: string; message: string }> {
    return this.post("/feedback", feedback);
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
