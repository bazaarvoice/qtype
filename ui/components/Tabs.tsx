"use client";

import { TabsList, TabsTrigger } from "@/components/ui/TabsContainer";
import { formatFlowName } from "./FlowTabsContainer";

import type { FlowMetadata } from "@/types";

interface FlowProps {
  flows: FlowMetadata[];
}

function Tabs({ flows }: FlowProps) {
  return (
    <TabsList
      className="grid w-full"
      style={{ gridTemplateColumns: `repeat(${flows.length}, minmax(0, 1fr))` }}
    >
      {flows.map(({ id }) => (
        <TabsTrigger key={id} value={id} className="text-sm">
          {formatFlowName(id)}
        </TabsTrigger>
      ))}
    </TabsList>
  );
}

export { Tabs };
