import { clsx, type ClassValue } from "clsx"
import { twMerge } from "tailwind-merge"
import { OpenAPIV3_1 } from "openapi-types"
import { SchemaProperty, OpenAPISpec } from "../types/Flow"

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

// =============================================================================
// OpenAPI Schema Processing Utilities
// =============================================================================

/**
 * Recursively dereferences $ref in schemas
 */
export function dereferenceSchema(schema: OpenAPIV3_1.SchemaObject | OpenAPIV3_1.ReferenceObject | undefined, spec: OpenAPISpec): SchemaProperty | null {
  if (!schema) return null
  
  // If this is a reference, resolve it
  if ('$ref' in schema) {
    const refPath = schema.$ref.replace('#/', '').split('/')
    let resolved: unknown = spec
    
    for (const segment of refPath) {
      resolved = (resolved as Record<string, unknown>)?.[segment]
    }
    
    // Recursively dereference the resolved schema
    return dereferenceSchema(resolved as OpenAPIV3_1.SchemaObject, spec)
  }
  
  // If this is an object with properties, dereference each property
  if (schema.type === 'object' && schema.properties) {
    const dereferencedProperties: Record<string, SchemaProperty> = {}
    
    for (const [key, value] of Object.entries(schema.properties)) {
      const resolved = dereferenceSchema(value, spec)
      if (resolved) {
        dereferencedProperties[key] = resolved
      }
    }
    
    return {
      ...schema,
      properties: dereferencedProperties
    } as SchemaProperty
  }
  
  // If this is an array, dereference the items
  if (schema.type === 'array' && schema.items) {
    const dereferencedItems = dereferenceSchema(schema.items, spec)
    return {
      ...schema,
      items: dereferencedItems
    } as SchemaProperty
  }
  
  // For primitive types or schemas without references, return as-is
  return schema as SchemaProperty
}

/**
 * Extracts and dereferences request schema from operation data
 */
export function extractRequestSchema(methodData: OpenAPIV3_1.OperationObject, spec: OpenAPISpec): SchemaProperty | null {
  if (!methodData.requestBody) return null
  
  const requestBody = methodData.requestBody as OpenAPIV3_1.RequestBodyObject
  const content = requestBody.content
  if (!content) return null
  
  // Get the first content type (usually application/json)
  const contentTypes = Object.keys(content)
  if (contentTypes.length === 0) return null
  
  const schema = content[contentTypes[0]]?.schema
  if (!schema) return null
  
  return dereferenceSchema(schema, spec)
}

/**
 * Extracts and dereferences response schema from operation data (200 response)
 */
export function extractResponseSchema(methodData: OpenAPIV3_1.OperationObject, spec: OpenAPISpec): SchemaProperty | null {
  if (!methodData.responses) return null
  
  const response200 = methodData.responses['200']
  if (!response200) return null
  
  const responseObj = response200 as OpenAPIV3_1.ResponseObject
  const content = responseObj.content
  if (!content) return null
  
  // Get the first content type (usually application/json)
  const contentTypes = Object.keys(content)
  if (contentTypes.length === 0) return null
  
  const schema = content[contentTypes[0]]?.schema
  if (!schema) return null
  
  return dereferenceSchema(schema, spec)
}
