'use client'

import { TabsList, TabsTrigger } from '@/components/ui/TabsContainer'
import type { FlowInfo } from '@/lib/apiClient'

interface FlowProps {
    flows: FlowInfo[];
}

function Tabs({flows}: FlowProps) {

    return (
            <TabsList className="grid w-full" style={{ gridTemplateColumns: `repeat(${flows.length}, minmax(0, 1fr))` }}>
                {flows.map(({id, name}) => (
                    <TabsTrigger key={id} value={id} className="text-sm">
                        {name}
                    </TabsTrigger>
                ))}
            </TabsList>
    )
}

export { Tabs }
