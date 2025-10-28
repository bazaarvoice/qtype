import { AlertCircle } from "lucide-react";

import { Alert, AlertDescription, AlertTitle } from "@/components/ui/Alert";
import { TabsContainer } from "@/components/ui/TabsContainer";
import { TabsContent } from "@/components/ui/TabsContainer";
import { useFlows } from "@/lib/hooks/useApi";

import { StreamFlow, ChatFlow, RestFlow } from "./flows";
import { Tabs } from "./Tabs";

const FLOW_ERROR_TITLE = "Failed to load flows";
const NO_FLOWS_FOUND_DESCRIPTION =
  "No flows were found in the API. Make sure your QType application has flows defined.";
const NO_FLOWS_FOUND_TITLE = "No flows found";
const LOADING_FLOWS = "Loading flows...";

/**
 * Formats a raw flow name for UI display
 * Converts snake_case to Title Case
 */
export function formatFlowName(rawFlowName: string): string {
  return rawFlowName
    .split("_")
    .map((word: string) => word.charAt(0).toUpperCase() + word.slice(1))
    .join(" ");
}

function FlowTabsContainer() {
  const { flows, isLoading, error } = useFlows();

  if (isLoading) {
    return <p className="text-muted-foreground text-sm">{LOADING_FLOWS}</p>;
  }

  if (error) {
    return (
      <Alert variant="destructive">
        <AlertCircle className="h-4 w-4" />
        <AlertTitle>{FLOW_ERROR_TITLE}</AlertTitle>
        <AlertDescription>{error.message}</AlertDescription>
      </Alert>
    );
  }

  if (!flows || !flows.length) {
    return (
      <Alert>
        <AlertCircle className="h-4 w-4" />
        <AlertTitle>{NO_FLOWS_FOUND_TITLE}</AlertTitle>
        <AlertDescription>{NO_FLOWS_FOUND_DESCRIPTION}</AlertDescription>
      </Alert>
    );
  }

  return (
    <TabsContainer defaultValue={flows[0]?.id} className="w-full">
      {flows.length > 1 && <Tabs flows={flows} />}

      {flows.map((flow) => (
        <TabsContent key={flow.id} value={flow.id} className="mt-6">
          {flow.interface_type === "Conversational" && <ChatFlow flow={flow} />}
          {flow.interface_type === "Complete" && <StreamFlow flow={flow} />}
          {!flow.interface_type && <RestFlow flow={flow} />}
        </TabsContent>
      ))}
    </TabsContainer>
  );
}

export { FlowTabsContainer };
