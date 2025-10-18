import { OpenAPIV3_1 } from "openapi-types";

type SchemaProperty = OpenAPIV3_1.SchemaObject & {
  qtype_type?: string
}

export type { SchemaProperty };