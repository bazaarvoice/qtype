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
import { Button } from '@/components/ui/Button'
import { Input } from '@/components/ui/Input'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/Card'
import { ScrollArea } from '@/components/ui/ScrollArea'
import { Send, Bot, Loader2, MessageSquarePlus, Paperclip} from 'lucide-react'
import { apiClient, type FlowInfo } from '@/lib/apiClient'
import { type FileAttachment } from '@/types/Flow'
import MessageBubble from '@/components/chat/MessageBubble'
import AttachmentDisplay from '@/components/chat/AttachmentDisplay'

const generateId = () => `${Date.now()}-${Math.random().toString(36).slice(2, 12)}`

function ChatFlow({ path, name, description }: FlowInfo) {
  const [conversationId, setConversationId] = useState(() => generateId())
  const [input, setInput] = useState('')
  const [selectedFiles, setSelectedFiles] = useState<FileAttachment[]>([])
  const [fileError, setFileError] = useState<string | null>(null)
  const [lastSubmission, setLastSubmission] = useState<{ input: string; files: FileAttachment[] } | null>(null)
  const inputRef = useRef<HTMLInputElement>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)
  const messagesEndRef = useRef<HTMLDivElement>(null)

  const transport = useMemo(() => new DefaultChatTransport({
    api: `${apiClient.getBaseUrl().replace(/\/$/, '')}${path}`,
  }), [path])

  const { messages, sendMessage, status, error, setMessages } = useChat({
    id: conversationId,
    transport,
    onFinish: () => {
      setLastSubmission(null)
    }
  })

  const isLoading = status === 'streaming' || status === 'submitted'
  const canSubmit = (status === 'ready' || status === 'error') && (input.trim() || selectedFiles.length > 0)

  // Auto-scroll to bottom when new messages arrive
  const scrollToBottom = useCallback(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [])

  // Scroll to bottom when messages change
  useEffect(() => {
    scrollToBottom()
  }, [messages, scrollToBottom])

  // Restore form when error occurs
  useEffect(() => {
    if (error && lastSubmission) {
      setInput(lastSubmission.input)
      setSelectedFiles(lastSubmission.files)
      setLastSubmission(null) // Clear after restoring
      setMessages(prev => {
        // remove empty assistant messages
        prev = prev.filter(msg => msg.parts.length > 0)
        // remove last message 
        if (prev.length > 0) {
          prev.pop()
        }
        return prev
      })
    }
  }, [error, lastSubmission])

  useEffect(() => {
    if (status === 'ready') inputRef.current?.focus()
  }, [status])

  const clearForm = useCallback(() => {
    setInput('')
    setSelectedFiles([])
    setFileError(null)
    if (fileInputRef.current) fileInputRef.current.value = ''
  }, [])

  const handleNewConversation = useCallback(() => {
    setConversationId(generateId())
    setMessages([])
    setLastSubmission(null)
    clearForm()
  }, [setMessages, clearForm])

  const convertFileToDataUrl = useCallback((file: File): Promise<string> => 
    new Promise((resolve, reject) => {
      const reader = new FileReader()
      reader.onload = () => resolve(reader.result as string)
      reader.onerror = reject
      reader.readAsDataURL(file)
    }), [])

  const handleFileSelect = useCallback(async (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files
    if (!files) return

    setFileError(null)

    try {
      const newFiles = await Promise.all(
        Array.from(files).map(async (file): Promise<FileAttachment> => {
          const url = await convertFileToDataUrl(file)
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
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Unknown error occurred'
      setFileError(`Failed to process files: ${errorMessage}`)
    }
  }, [convertFileToDataUrl])

  const removeFile = useCallback((index: number) => {
    setSelectedFiles(prev => prev.filter((_, i) => i !== index))
  }, [])

  const clearFiles = useCallback(() => {
    setSelectedFiles([])
    if (fileInputRef.current) fileInputRef.current.value = ''
  }, [])

  const handleSubmit = useCallback(async (e: React.FormEvent) => {
    e.preventDefault()
    if (!canSubmit) return

    const messageContent = input.trim()
    const filesToSend = [...selectedFiles]
    
    // Store the submission for potential error recovery
    setLastSubmission({ input: messageContent, files: filesToSend })
    
    // Clear the form immediately
    clearForm()
    
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
  }, [canSubmit, input, selectedFiles, sendMessage, clearForm])

  return (
    <Card className="w-full max-w-4xl mx-auto h-[calc(100vh-12rem)] flex flex-col">
      <CardHeader className="flex-shrink-0">
        <div className="flex items-center justify-between">
          <div>
            <CardTitle className="flex items-center gap-2">
              <Bot className="h-5 w-5" />
              {name}
            </CardTitle>
            {description && <CardDescription>{description}</CardDescription>}
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
                <p>Start a conversation!</p>
              </div>
            ) : (
              messages.map(message => (
                <MessageBubble key={message.id} message={message} />
              ))
            )}
            <div ref={messagesEndRef} />
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

export { ChatFlow }