import { useMemo } from 'react'
import { Avatar, AvatarFallback } from '@/components/ui/avatar'
import { Bot, User } from 'lucide-react'
import FileDisplay from './FileDisplay'

interface FileAttachment {
  type: 'file'
  mediaType: string
  filename: string
  url: string
  size?: number
}

interface MessageBubbleProps {
  message: any
}

export default function MessageBubble({ message }: MessageBubbleProps) {
  const isUser = message.role === 'user'
  
  // Extract content with better type safety
  const textContent = useMemo(() => {
    return message.content || 
      message.parts?.filter((p: any) => p.type === 'text').map((p: any) => p.text).join('') ||
      ''
  }, [message])
  
  // Extract file attachments with better type safety
  const fileAttachments = useMemo(() => {
    return message.files || 
      message.experimental_attachments ||
      message.parts?.filter((p: any) => p.type === 'file') ||
      []
  }, [message])
  
  return (
    <div className={`flex gap-3 w-full ${isUser ? 'justify-end' : 'justify-start'}`}>
      {!isUser && (
        <Avatar className="h-8 w-8 flex-shrink-0">
          <AvatarFallback><Bot className="h-4 w-4" /></AvatarFallback>
        </Avatar>
      )}
      
      <div className="flex-1 max-w-[75%] space-y-2">
        {textContent && (
          <div className={`rounded-lg px-3 py-2 text-sm whitespace-pre-wrap break-words ${
            isUser ? 'bg-primary text-primary-foreground' : 'bg-muted'
          }`}>
            {textContent}
          </div>
        )}
        
        {fileAttachments.map((file: FileAttachment, index: number) => (
          <FileDisplay
            key={`${file.filename}-${index}`}
            mediaType={file.mediaType}
            filename={file.filename}
            url={file.url}
            size={file.size}
          />
        ))}
      </div>
      
      {isUser && (
        <Avatar className="h-8 w-8 flex-shrink-0">
          <AvatarFallback><User className="h-4 w-4" /></AvatarFallback>
        </Avatar>
      )}
    </div>
  )
}
