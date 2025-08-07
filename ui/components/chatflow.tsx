/**
 * ChatFlow Component
 * 
 * Provides a chat interface for ChatFlow endpoints using Vercel AI SDK with DefaultChatTransport
 */

'use client'

import { useChat } from '@ai-sdk/react'
import { DefaultChatTransport } from 'ai'
import { useState, useCallback, useMemo, useRef } from 'react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Avatar, AvatarFallback } from '@/components/ui/avatar'
import { Send, User, Bot, Loader2 } from 'lucide-react'
import { apiClient, type FlowInfo } from '@/lib/api-client'

interface ChatFlowProps {
  flow: FlowInfo
}

// Helper functions outside component to prevent recreations
const getMessageText = (message: any): string => {
  return message.parts
    ?.filter((part: any) => part.type === 'text')
    .map((part: any) => part.text)
    .join('') || ''
}

const EmptyState = ({ flowName }: { flowName: string }) => (
  <div className="text-center text-muted-foreground py-8">
    <Bot className="h-12 w-12 mx-auto mb-4 opacity-50" />
    <p>Start a conversation with {flowName}</p>
  </div>
)

const MessageBubble = ({ message }: { message: any }) => {
  const isUser = message.role === 'user'
  
  return (
    <div className={`flex gap-3 w-full ${isUser ? 'justify-end' : 'justify-start'}`}>
      {!isUser && (
        <Avatar className="h-8 w-8 flex-shrink-0">
          <AvatarFallback><Bot className="h-4 w-4" /></AvatarFallback>
        </Avatar>
      )}
      
      <div className={`flex-1 max-w-[75%] rounded-lg px-3 py-2 text-sm whitespace-pre-wrap break-words ${
        isUser ? 'bg-primary text-primary-foreground' : 'bg-muted'
      }`}>
        {getMessageText(message)}
      </div>
      
      {isUser && (
        <Avatar className="h-8 w-8 flex-shrink-0">
          <AvatarFallback><User className="h-4 w-4" /></AvatarFallback>
        </Avatar>
      )}
    </div>
  )
}

export default function ChatFlow({ flow }: ChatFlowProps) {
  const [input, setInput] = useState('')
  const sentMessageIdsRef = useRef(new Set<string>())

  const transport = useMemo(() => new DefaultChatTransport({
    api: `${apiClient.getBaseUrl().replace(/\/$/, '')}${flow.path}`,
    prepareSendMessagesRequest: ({ messages, id, trigger, messageId }) => {
      const newMessages = messages.filter(msg => 
        msg.role === 'user' && !sentMessageIdsRef.current.has(msg.id)
      )
      
      newMessages.forEach(msg => sentMessageIdsRef.current.add(msg.id))
      
      return { body: { messages: newMessages, id, trigger, messageId } }
    },
  }), [flow.path])

  const { messages, sendMessage, status, error } = useChat({
    id: flow.id,
    transport,
  })

  const handleSubmit = useCallback((e: React.FormEvent) => {
    e.preventDefault()
    const trimmedInput = input.trim()
    if (!trimmedInput || status !== 'ready') return
    
    sendMessage({ text: trimmedInput })
    setInput('')
  }, [input, status, sendMessage])

  const isLoading = status === 'streaming' || status === 'submitted'

  return (
    <Card className="w-full max-w-4xl mx-auto h-[600px] flex flex-col">
      <CardHeader className="flex-shrink-0">
        <CardTitle className="flex items-center gap-2">
          <Bot className="h-5 w-5" />
          {flow.name}
        </CardTitle>
        {flow.description && <CardDescription>{flow.description}</CardDescription>}
      </CardHeader>
      
      <CardContent className="flex-1 flex flex-col p-0">
        <ScrollArea className="flex-1 p-4">
          <div className="space-y-4">
            {messages.length === 0 ? (
              <EmptyState flowName={flow.name} />
            ) : (
              messages.map(message => (
                <MessageBubble key={message.id} message={message} />
              ))
            )}
          </div>
        </ScrollArea>
        
        <div className="border-t p-4">
          {error && (
            <div className="mb-3 p-2 bg-destructive/10 text-destructive text-sm rounded">
              Error: {error.message}
            </div>
          )}
          
          <form onSubmit={handleSubmit} className="flex gap-2">
            <Input
              value={input}
              onChange={(e) => setInput(e.target.value)}
              disabled={status !== 'ready'}
              placeholder="Type your message..."
              className="flex-1"
              autoFocus
            />
            <Button 
              type="submit" 
              disabled={status !== 'ready' || !input.trim()}
              size="icon"
              aria-label="Send message"
            >
              {isLoading ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <Send className="h-4 w-4" />
              )}
            </Button>
          </form>
        </div>
      </CardContent>
    </Card>
  )
}