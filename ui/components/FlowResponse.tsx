/**
 * Flow Response Component
 *
 * Renders a single flow response as cards
 */

"use client";

import FlowResponseCards from "./FlowResponseCards";

import type { SchemaProperty, ResponseData } from "@/types";

interface FlowResponseProps {
  responseSchema?: SchemaProperty | null;
  responseData?: ResponseData;
}

export default function FlowResponse({
  responseSchema,
  responseData,
}: FlowResponseProps) {
  return (
    <FlowResponseCards
      responseSchema={responseSchema}
      responseData={responseData}
    />
  );
}
