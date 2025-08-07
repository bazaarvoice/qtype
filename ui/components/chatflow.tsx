/**
 * ChatFlow Component
 * 
 * Provides a chat interface for ChatFlow endpoints using Vercel AI SDK with DefaultChatTransport
 */

'use client'

import { useChat } from '@ai-sdk/react'
import { DefaultChatTransport } from 'ai'
import { useRef, useState } from 'react'
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

export default function ChatFlow({ flow }: ChatFlowProps) {
  const [input, setInput] = useState('')
  const [sentMessageIds, setSentMessageIds] = useState<Set<string>>(new Set())

  const sentMessageIdsRef = useRef(sentMessageIds)
  
  // Keep ref in sync with state
  sentMessageIdsRef.current = sentMessageIds

  const baseUrl = `${apiClient.getBaseUrl().replace(/\/$/, '')}${flow.path}`
  const { messages, sendMessage, status, error } = useChat({
    id: flow.id,
    transport: new DefaultChatTransport({
      api: baseUrl,
      prepareSendMessagesRequest: ({ messages, id, trigger, messageId }) => {
        // Find messages that haven't been sent yet
        
        const newMessages = messages.filter(msg => !sentMessageIdsRef.current.has(msg.id) && msg.role === 'user')
        
        // Mark these messages as sent
        setSentMessageIds(prev => {
          const updated = new Set(prev)
          newMessages.forEach(msg => updated.add(msg.id))
          return updated
        })
        
        return {
          body: {
            messages: newMessages,
            id,
            trigger: trigger,
            messageId
          }
        }
      },
    })
  })

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (!input.trim() || status !== 'ready') return
    
    sendMessage({ text: input })
    setInput('')
  }

  return (
    <Card className="w-full max-w-4xl mx-auto h-[600px] flex flex-col">
      <CardHeader className="flex-shrink-0">
        <CardTitle className="flex items-center gap-2">
          <Bot className="h-5 w-5" />
          {flow.name}
        </CardTitle>
        {flow.description && (
          <CardDescription>{flow.description}</CardDescription>
        )}
      </CardHeader>
      
      <CardContent className="flex-1 flex flex-col p-0">
        {/* Messages Area */}
        <ScrollArea className="flex-1 p-4">
          <div className="space-y-4">
            {messages.length === 0 && (
              <div className="text-center text-muted-foreground py-8">
                <Bot className="h-12 w-12 mx-auto mb-4 opacity-50" />
                <p>Start a conversation with {flow.name}</p>
              </div>
            )}
            
            {messages.map((message) => (
              <div
                key={message.id}
                className={`flex gap-3 w-full ${
                  message.role === 'user' ? 'justify-end' : 'justify-start'
                }`}
              >
                {message.role === 'assistant' && (
                  <Avatar className="h-8 w-8 flex-shrink-0">
                    <AvatarFallback>
                      <Bot className="h-4 w-4" />
                    </AvatarFallback>
                  </Avatar>
                )}
                
                <div
                  className={`flex-1 max-w-[75%] rounded-lg px-3 py-2 break-words overflow-hidden ${
                    message.role === 'user'
                      ? 'bg-primary text-primary-foreground'
                      : 'bg-muted'
                  }`}
                >
                  <div className="text-sm whitespace-pre-wrap break-words overflow-wrap-anywhere">
                    {message.parts
                      .filter((part: any) => part.type === 'text')
                      .map((part: any, index: number) => (
                        <span key={index}>{part.text}</span>
                      ))}
                  </div>
                </div>
                
                {message.role === 'user' && (
                  <Avatar className="h-8 w-8 flex-shrink-0">
                    <AvatarFallback>
                      <User className="h-4 w-4" />
                    </AvatarFallback>
                  </Avatar>
                )}
              </div>
            ))}
          </div>
        </ScrollArea>
        
        {/* Input Area */}
        <div className="border-t p-4">
          {error && (
            <div className="mb-3 p-2 bg-destructive/10 text-destructive text-sm rounded flex items-center justify-between">
              <span>Error: {error.message}</span>
              <Button
                variant="outline"
                size="sm"
                onClick={() => window.location.reload()}
              >
                Retry
              </Button>
            </div>
          )}
          
          <form onSubmit={handleSubmit} className="flex gap-2">
            <Input
              value={input}
              onChange={(e) => setInput(e.target.value)}
              disabled={status !== 'ready'}
              placeholder="Type your message..."
              className="flex-1"
            />
            <Button 
              type="submit" 
              disabled={status !== 'ready' || !input.trim()}
              size="icon"
            >
              {(status === 'streaming' || status === 'submitted') ? (
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