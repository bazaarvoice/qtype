/**
 * Flow Tabs Component
 * 
 * Creates tabs for each flow endpoint found in the OpenAPI specification
 */

'use client'

import { useOpenApiSpec } from '@/lib/hooks/use-api'
import { extractFlowsFromSpec, type OpenAPISpec } from '@/lib/api-client'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert'
import { AlertCircle } from 'lucide-react'
import Flow from './flow'
import ChatFlow from './chatflow'

export default function FlowTabs() {
    const { spec, isLoading, error } = useOpenApiSpec()

    // Extract flows from the OpenAPI spec (names are already formatted for display)
    const flows = extractFlowsFromSpec(spec || {} as OpenAPISpec)

    if (isLoading) {
        return (
            <p className="text-muted-foreground text-sm">Loading flows...</p>
        )
    }

    if (error) {
        return (
            <Alert variant="destructive">
                <AlertCircle className="h-4 w-4" />
                <AlertTitle>Failed to load flows</AlertTitle>
                <AlertDescription>
                    {error.message}
                </AlertDescription>
            </Alert>
        )
    }

    if (!flows.length) {
        return (
            <Alert>
                <AlertCircle className="h-4 w-4" />
                <AlertTitle>No flows found</AlertTitle>
                <AlertDescription>
                    No flows were found in the API specification. Make sure your FastAPI server has endpoints tagged with &quot;flow&quot; or paths starting with &quot;/flows/&quot;.
                </AlertDescription>
            </Alert>
        )
    }

    // If there's only one flow, show it directly without tabs
    if (flows.length === 1) {
        const flow = flows[0]
        return (
            <div className="w-full">
                {flow.mode === 'Chat' ? <ChatFlow flow={flow} /> : <Flow flow={flow} />}
            </div>
        )
    } else {
        return (
            <div className="w-full">
                <Tabs defaultValue={flows[0]?.id} className="w-full">
                <TabsList className="grid w-full" style={{ gridTemplateColumns: `repeat(${flows.length}, minmax(0, 1fr))` }}>
                    {flows.map((flow) => (
                        <TabsTrigger key={flow.id} value={flow.id} className="text-sm">
                            {flow.name}
                        </TabsTrigger>
                    ))}
                </TabsList>

                {flows.map((flow) => (
                    <TabsContent key={flow.id} value={flow.id} className="mt-6">
                        {flow.mode === 'Chat' ? <ChatFlow flow={flow} /> : <Flow flow={flow} />}
                    </TabsContent>
                ))}
            </Tabs>
        </div>
        )
    }
}
