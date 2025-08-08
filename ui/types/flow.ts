/**
 * Common types for flow components using OpenAPI 3.1 standard types
 */

import type { OpenAPIV3_1 } from 'openapi-types'

// Use OpenAPI standard schema object with our custom qtype_type extension
export type SchemaProperty = OpenAPIV3_1.SchemaObject & {
  qtype_type?: string
}

// Flow input value types
export type FlowInputValue = string | number | boolean | null | undefined

// Flow inputs collection
// Type for the input values in a flow
export type FlowInputValues = Record<string, FlowInputValue>

// Generic response data
export type ResponseData = Record<string, unknown>

// OpenAPI spec type alias for convenience
export type OpenAPISpec = OpenAPIV3_1.Document

// File attachment type for chat components
export interface FileAttachment {
  type: 'file'
  mediaType: string
  filename: string
  url: string
  size?: number
}
