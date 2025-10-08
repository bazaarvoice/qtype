import ReactMarkdown from "react-markdown"
import remarkGfm from "remark-gfm"

function MarkdownContainer({ children }: { children: string }) {
  return(
  <div className="bg-gray-50 dark:bg-gray-900 p-3 rounded">
      <ReactMarkdown 
        remarkPlugins={[remarkGfm]}
        components={{
          code: ({ children, ...props }) => {
            const isInline = !props.className
            return isInline ? (
              <code className="bg-gray-100 dark:bg-gray-800 px-1 py-0.5 rounded text-xs" {...props}>
                {children}
              </code>
            ) : (
              <pre className="bg-gray-100 dark:bg-gray-800 p-2 rounded text-xs overflow-x-auto">
                <code {...props}>
                  {children}
                </code>
              </pre>
            )
          },
          // Style tables
          table: ({ children }) => (
            <div className="overflow-x-auto mb-4">
              <table className="min-w-full border-collapse border border-gray-300 dark:border-gray-600">
                {children}
              </table>
            </div>
          ),
          thead: ({ children }) => (
            <thead className="bg-gray-100 dark:bg-gray-800">
              {children}
            </thead>
          ),
          tbody: ({ children }) => (
            <tbody>
              {children}
            </tbody>
          ),
          tr: ({ children }) => (
            <tr className="border-b border-gray-200 dark:border-gray-700">
              {children}
            </tr>
          ),
          th: ({ children }) => (
            <th className="px-3 py-2 text-left text-xs font-medium text-gray-700 dark:text-gray-300 border-r border-gray-300 dark:border-gray-600 last:border-r-0">
              {children}
            </th>
          ),
          td: ({ children }) => (
            <td className="px-3 py-2 text-xs text-gray-600 dark:text-gray-400 border-r border-gray-300 dark:border-gray-600 last:border-r-0">
              {children}
            </td>
          ),
          // Style headings with better hierarchy
          h1: ({ children }) => <h1 className="text-xl font-bold mb-4 mt-6 text-gray-900 dark:text-gray-100 border-b border-gray-200 dark:border-gray-700 pb-2">{children}</h1>,
          h2: ({ children }) => <h2 className="text-lg font-semibold mb-3 mt-5 text-gray-900 dark:text-gray-100">{children}</h2>,
          h3: ({ children }) => <h3 className="text-base font-semibold mb-2 mt-4 text-gray-800 dark:text-gray-200">{children}</h3>,
          h4: ({ children }) => <h4 className="text-sm font-medium mb-2 mt-3 text-gray-700 dark:text-gray-300">{children}</h4>,
          // Fix list styling to remove errant bullets
          ul: ({ children }) => <ul className="mb-3 pl-0 space-y-1 text-gray-800 dark:text-gray-200">{children}</ul>,
          ol: ({ children }) => <ol className="mb-3 pl-0 space-y-1 text-gray-800 dark:text-gray-200">{children}</ol>,
          li: ({ children }) => <li className="flex items-start ml-4"><span className="mr-2 text-gray-500 dark:text-gray-400 select-none">•</span><span className="flex-1">{children}</span></li>,
          // Style paragraphs
          p: ({ children }) => <p className="mb-3 text-gray-800 dark:text-gray-200 leading-relaxed">{children}</p>,
          // Style strong text
          strong: ({ children }) => <strong className="font-semibold text-gray-900 dark:text-gray-100">{children}</strong>,
          // Style blockquotes
          blockquote: ({ children }) => <blockquote className="border-l-4 border-gray-300 dark:border-gray-600 pl-4 italic mb-3 text-gray-700 dark:text-gray-300">{children}</blockquote>,
        }}
      >
        {children}
      </ReactMarkdown>
    </div>
  )}

export { MarkdownContainer}