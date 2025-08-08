import { Paperclip } from 'lucide-react'

interface FileDisplayProps {
  mediaType?: string
  filename?: string
  url?: string
  size?: number
}

const formatFileSize = (bytes: number) => `${(bytes / (1024 * 1024)).toFixed(1)} MB`

export default function FileDisplay({ mediaType, filename, url, size }: FileDisplayProps) {
  if (!url) return null

  const isImage = mediaType?.startsWith('image/')
  
  return (
    <div className="border rounded p-2 bg-background">
      {isImage ? (
        <img
          src={url}
          alt={filename || 'Attached image'}
          className="max-w-full h-auto rounded"
          style={{ maxHeight: '200px' }}
        />
      ) : (
        <div className="flex items-center gap-2 text-sm">
          <Paperclip className="h-4 w-4" />
          <span>{filename || 'Attachment'}</span>
          {mediaType && (
            <span className="text-xs text-muted-foreground">({mediaType})</span>
          )}
          {size && (
            <span className="text-xs text-muted-foreground">
              - {formatFileSize(size)}
            </span>
          )}
        </div>
      )}
    </div>
  )
}
