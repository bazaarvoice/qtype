import { useMemo } from 'react'
import { Avatar, AvatarFallback } from '@/components/ui/avatar'
import { Bot, User } from 'lucide-react'
import { type FileAttachment } from '@/types/flow'
import FileDisplay from './FileDisplay'

interface MessagePart {
  type: string
  text?: string
}

interface Message {
  role: string
  content?: string
  parts?: (MessagePart | FileAttachment)[]
  files?: FileAttachment[]
  experimental_attachments?: FileAttachment[]
}

interface MessageBubbleProps {
  message: Message
}

export default function MessageBubble({ message }: MessageBubbleProps) {
  const isUser = message.role === 'user'
  
  const textContent = useMemo(() => {
    return message.content || 
      message.parts?.filter(p => p.type === 'text').map(p => 'text' in p ? p.text : '').join('') ||
      ''
  }, [message])
  
  const fileAttachments = useMemo((): FileAttachment[] => {
    const files = message.files || 
      message.experimental_attachments ||
      message.parts?.filter((p): p is FileAttachment => p.type === 'file') ||
      []
    return files
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
        
        {fileAttachments.map((file, index) => (
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
