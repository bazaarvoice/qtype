import { AlertCircle } from "lucide-react";

import { Alert, AlertDescription, AlertTitle } from "@/components/ui/Alert";
import { TabsContainer } from "@/components/ui/TabsContainer";
import { TabsContent } from "@/components/ui/TabsContainer";
import { extractFlowsFromSpec } from "@/lib/apiClient";
import { useOpenApiSpec } from "@/lib/hooks/useApi";

import { StreamFlow, ChatFlow } from "./flows";
import { Tabs } from "./Tabs";

import type { OpenAPISpec } from "@/types";

const FLOW_ERROR_TITLE = "Failed to load flows";
const NO_FLOWS_FOUND_DESCRIPTION =
  "No flows were found in the API specification. Make sure your FastAPI server has endpoints tagged with &quot;flow&quot; or paths starting with &quot;/flows/&quot;.";
const NO_FLOWS_FOUND_TITLE = "No flows found";
const LOADING_FLOWS = "Loading flows...";

function FlowTabsContainer() {
  const { spec, isLoading, error } = useOpenApiSpec();
  const flows = extractFlowsFromSpec(spec || ({} as OpenAPISpec));

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

  if (!flows.length) {
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
          {flow.mode === "Chat" && <ChatFlow {...flow} />}
          {flow.mode === "Complete" && <StreamFlow {...flow} />}
        </TabsContent>
      ))}
    </TabsContainer>
  );
}

export { FlowTabsContainer };
