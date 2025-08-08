/**
 * ChatFlow Component
 * 
 * Provides  const { messages, sendMessage, status, error, reload } = useChat({
    id: flow.id,
    transport
  })

  const isReady = status === 'ready'
  const isLoading = status === 'streaming' || status === 'submitted'
  const hasError = status === 'error' || error
  const canSubmit = (isReady || hasError) && input.trim()interface for ChatFlow endpoints using Vercel AI SDK with DefaultChatTransport
 */

'use client'

import { useChat } from '@ai-sdk/react'
import { DefaultChatTransport } from 'ai'
import { useState, useCallback, useMemo } from 'react'
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

  const transport = useMemo(() => new DefaultChatTransport({
    api: `${apiClient.getBaseUrl().replace(/\/$/, '')}${flow.path}`,
  }), [flow])

  const { messages, sendMessage, status, error, setMessages } = useChat({
    id: flow.id,
    transport,
    onError: (error) => {
      // Find and remove user messages from the end of the array, repopulate input
      setMessages(prevMessages => {
        // iterate backwards over the messages array while the last message is from the user
        // keep the messages you pop in a temp array to repopulate the input later
        const tempArray: typeof prevMessages = []
        while (prevMessages.length > 0 && prevMessages[prevMessages.length - 1].role === 'user') {
          tempArray.push(prevMessages.pop()!)
        }

        // Repopulate input with the text from these user messages
        if (tempArray.length > 0) {
          // TODO: handle non text inputs
          const combinedText = tempArray
            .map(msg => msg.parts?.filter(p => p.type === 'text').map(p => p.text).join('') || '')
            .join(' ')
          setInput(combinedText)
        }

        // Return messages up to (but not including) the failed user messages
        return prevMessages
      })
    }
  })

  const isLoading = status === 'streaming' || status === 'submitted'
  const canSubmit = (status === 'ready' && input.trim()) || (status === 'error' || error)

  const handleSubmit = useCallback((e: React.FormEvent) => {
    e.preventDefault()
    if (!canSubmit) return

    sendMessage({ text: input.trim() })
    setInput('')
  }, [input, canSubmit, sendMessage])

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
        <ScrollArea>
          <div className="space-y-4">
            {messages.length === 0 ? (
              <div className="text-center text-muted-foreground py-8">
                <Bot className="h-12 w-12 mx-auto mb-4 opacity-50" />
                <p>Start a conversation with {flow.name}</p>
              </div>
            ) : (
              messages.map(message => {
                const isUser = message.role === 'user'
                const text = message.parts?.filter(p => p.type === 'text').map(p => p.text).join('') || ''

                return (
                  <div key={message.id} className={`flex gap-3 w-full ${isUser ? 'justify-end' : 'justify-start'}`}>
                    {!isUser && <Avatar className="h-8 w-8 flex-shrink-0"><AvatarFallback><Bot className="h-4 w-4" /></AvatarFallback></Avatar>}
                    <div className={`flex-1 max-w-[75%] rounded-lg px-3 py-2 text-sm whitespace-pre-wrap break-words ${isUser ? 'bg-primary text-primary-foreground' : 'bg-muted'}`}>
                      {text}
                    </div>
                    {isUser && <Avatar className="h-8 w-8 flex-shrink-0"><AvatarFallback><User className="h-4 w-4" /></AvatarFallback></Avatar>}
                  </div>
                )
              })
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
              disabled={isLoading}
              placeholder="Type your message..."
              className="flex-1"
              autoFocus
            />
            <Button
              type="submit"
              disabled={!canSubmit}
              size="icon"
              aria-label="Send message"
            >
              {isLoading ? <Loader2 className="h-4 w-4 animate-spin" /> : <Send className="h-4 w-4" />}
            </Button>
          </form>
        </div>
      </CardContent>
    </Card>
  )
}