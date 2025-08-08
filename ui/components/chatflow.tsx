/**
 * ChatFlow Component
 * 
 * Provides a chat interface for QType flows using the Vercel AI SDK.
 * Supports file attachments and follows the backend's expected message format.
 */

'use client'

import { useChat } from '@ai-sdk/react'
import { DefaultChatTransport } from 'ai'
import { useState, useCallback, useMemo, useEffect, useRef } from 'react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Send, Bot, Loader2, MessageSquarePlus, Paperclip} from 'lucide-react'
import { apiClient, type FlowInfo } from '@/lib/api-client'
import { type FileAttachment } from '@/types/flow'
import MessageBubble from '@/components/chat/MessageBubble'
import AttachmentDisplay from '@/components/chat/AttachmentDisplay'

interface ChatFlowProps {
  flow: FlowInfo
}

const generateId = () => `${Date.now()}-${Math.random().toString(36).slice(2, 12)}`

const fileToDataUrl = (file: File): Promise<string> => 
  new Promise((resolve, reject) => {
    const reader = new FileReader()
    reader.onload = () => resolve(reader.result as string)
    reader.onerror = reject
    reader.readAsDataURL(file)
  })

export default function ChatFlow({ flow }: ChatFlowProps) {
  const [conversationId, setConversationId] = useState(() => generateId())
  const [input, setInput] = useState('')
  const [selectedFiles, setSelectedFiles] = useState<FileAttachment[]>([])
  const [fileError, setFileError] = useState<string | null>(null)
  const lastSubmittedInputRef = useRef('')
  const lastSubmittedFilesRef = useRef<FileAttachment[]>([])
  const inputRef = useRef<HTMLInputElement>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)

  const transport = useMemo(() => new DefaultChatTransport({
    api: `${apiClient.getBaseUrl().replace(/\/$/, '')}${flow.path}`,
  }), [flow.path])

  const { messages, sendMessage, status, error, setMessages } = useChat({
    id: conversationId,
    transport,
    onFinish: () => {
      // Clear the stored values on successful completion
      lastSubmittedInputRef.current = ''
      lastSubmittedFilesRef.current = []
    }
  })

  // Restore form when error occurs
  useEffect(() => {
    if (error && lastSubmittedInputRef.current) {
      setInput(lastSubmittedInputRef.current)
      setSelectedFiles(lastSubmittedFilesRef.current)
      
      // Remove failed messages (empty assistant message and the user message that failed)
      setMessages(prevMessages => {
        let filteredMessages = [...prevMessages]
        
        // Remove any empty assistant messages from the end
        while (filteredMessages.length > 0) {
          const lastMessage = filteredMessages[filteredMessages.length - 1]
          if (lastMessage.role === 'assistant' && lastMessage.parts.length === 0) {
            filteredMessages = filteredMessages.slice(0, -1)
          } else {
            break
          }
        }
        
        // Remove the last user message if it exists
        if (filteredMessages.length > 0 && filteredMessages[filteredMessages.length - 1].role === 'user') {
          filteredMessages = filteredMessages.slice(0, -1)
        }
        
        return filteredMessages
      })
    }
  }, [error, setMessages])

  const isLoading = status === 'streaming' || status === 'submitted'
  const canSubmit = (status === 'ready' || status === 'error') && (input.trim() || selectedFiles.length)

  useEffect(() => {
    if (status === 'ready') inputRef.current?.focus()
  }, [status])

  const resetForm = useCallback(() => {
    setInput('')
    setSelectedFiles([])
    setFileError(null)
    if (fileInputRef.current) fileInputRef.current.value = ''
  }, [])

  const resetAll = useCallback(() => {
    resetForm()
    lastSubmittedInputRef.current = ''
    lastSubmittedFilesRef.current = []
  }, [resetForm])

  const handleFileSelect = useCallback(async (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files
    if (!files) return

    setFileError(null) // Clear any previous errors

    try {
      const newFiles = await Promise.all(
        Array.from(files).map(async (file): Promise<FileAttachment> => {
          const url = await fileToDataUrl(file)
          return {
            type: 'file',
            mediaType: file.type || 'application/octet-stream',
            filename: file.name,
            url,
            size: file.size,
          }
        })
      )
      setSelectedFiles(prev => [...prev, ...newFiles])
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Unknown error occurred'
      setFileError(`Failed to process files: ${errorMessage}`)
    }
  }, [])

  const removeFile = useCallback((index: number) => {
    setSelectedFiles(prev => prev.filter((_, i) => i !== index))
  }, [])

  const clearFiles = useCallback(() => {
    setSelectedFiles([])
    if (fileInputRef.current) fileInputRef.current.value = ''
  }, [])

  const handleNewConversation = useCallback(() => {
    setConversationId(generateId())
    setMessages([])
    resetAll()
  }, [setMessages, resetAll])

  const handleSubmit = useCallback(async (e: React.FormEvent) => {
    e.preventDefault()
    if (!canSubmit) return

    const messageContent = input.trim()
    const filesToSend = [...selectedFiles]
    
    // Store the current input and files before clearing the form
    lastSubmittedInputRef.current = messageContent
    lastSubmittedFilesRef.current = filesToSend
    
    // Clear the form immediately
    resetForm()
    
    if (filesToSend.length > 0) {
      await sendMessage({
        role: 'user',
        parts: [
          { type: 'text', text: messageContent || "[Files attached]" },
          ...filesToSend.map(file => ({
            type: 'file' as const,
            mediaType: file.mediaType,
            filename: file.filename,
            url: file.url,
            size: file.size,
          }))
        ]
      })
    } else {
      await sendMessage({ text: messageContent })
    }
  }, [canSubmit, input, selectedFiles, sendMessage, resetForm])

  return (
    <Card className="w-full max-w-4xl mx-auto h-[calc(100vh-12rem)] flex flex-col">
      <CardHeader className="flex-shrink-0">
        <div className="flex items-center justify-between">
          <div>
            <CardTitle className="flex items-center gap-2">
              <Bot className="h-5 w-5" />
              {flow.name}
            </CardTitle>
            {flow.description && <CardDescription>{flow.description}</CardDescription>}
          </div>
          <Button
            variant="outline"
            size="sm"
            onClick={handleNewConversation}
            disabled={isLoading}
            className="flex items-center gap-2"
          >
            <MessageSquarePlus className="h-4 w-4" />
            New Conversation
          </Button>
        </div>
      </CardHeader>

      <CardContent className="flex-1 flex flex-col p-0 min-h-0">
        <ScrollArea className="flex-1 min-h-0">
          <div className="space-y-4 p-4">
            {messages.length === 0 ? (
              <div className="flex flex-col items-center justify-center min-h-[400px] text-center text-muted-foreground">
                <Bot className="h-12 w-12 mb-4 opacity-50" />
                <p>Start a conversation with {flow.name}</p>
              </div>
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

          {fileError && (
            <div className="mb-3 p-2 bg-destructive/10 text-destructive text-sm rounded">
              {fileError}
            </div>
          )}

          {selectedFiles.length > 0 && (
            <AttachmentDisplay 
              files={selectedFiles} 
              onRemoveFile={removeFile} 
              onClearAll={clearFiles} 
            />
          )}

          <form onSubmit={handleSubmit} className="flex gap-2">
            <input
              ref={fileInputRef}
              type="file"
              multiple
              onChange={handleFileSelect}
              className="hidden"
              accept="*"
            />
            <Button
              type="button"
              variant="outline"
              size="icon"
              onClick={() => fileInputRef.current?.click()}
              disabled={isLoading}
              aria-label="Attach file"
            >
              <Paperclip className="h-4 w-4" />
            </Button>
            <Input
              ref={inputRef}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter' && !e.shiftKey && canSubmit) {
                  e.preventDefault()
                  handleSubmit(e)
                }
              }}
              disabled={isLoading}
              placeholder="Type your message... (Enter to send, Shift+Enter for new line)"
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