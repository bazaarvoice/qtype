import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

import type { Components } from "react-markdown";

interface MarkdownContainerProps {
  children: string;
  theme?: "light" | "dark";
  chatBubble?: boolean;
  className?: string;
}
function MarkdownContainer({
  children,
  theme = "light",
  chatBubble = false,
  className,
}: MarkdownContainerProps) {
  const rootClass =
    `${theme === "dark" ? "dark " : ""}${className ?? ""}`.trim();

  const bg = chatBubble
    ? theme === "dark"
      ? "bg-primary"
      : "bg-muted"
    : "bg-transparent";

  return (
    <div className={`${bg} rounded-lg px-3 py-2`}>
      <div className={rootClass}>
        <ReactMarkdown
          remarkPlugins={[remarkGfm]}
          components={markdownComponents}
        >
          {children}
        </ReactMarkdown>
      </div>
    </div>
  );
}

const markdownComponents: Components = {
  code: ({ children: codeChildren, ...props }) => {
    const isInline = !props.className;
    return isInline ? (
      <code
        className="bg-gray-100 dark:bg-gray-800 px-1 py-0.5 rounded text-xs"
        {...props}
      >
        {codeChildren}
      </code>
    ) : (
      <pre className="bg-gray-100 dark:bg-gray-800 p-2 pb-0 rounded text-xs overflow-x-auto last:mb-0 last:pb-0">
        <code {...props}>{codeChildren}</code>
      </pre>
    );
  },
  table: ({ children: tableChildren }) => (
    <div className="overflow-x-auto mb-4 last:mb-0">
      <table className="min-w-full border-collapse border border-gray-300 dark:border-gray-600">
        {tableChildren}
      </table>
    </div>
  ),
  thead: ({ children: theadChildren }) => (
    <thead className="bg-gray-100 dark:bg-gray-800">{theadChildren}</thead>
  ),
  tbody: ({ children: tbodyChildren }) => <tbody>{tbodyChildren}</tbody>,
  tr: ({ children: trChildren }) => (
    <tr className="border-b border-gray-200 dark:border-gray-700">
      {trChildren}
    </tr>
  ),
  th: ({ children: thChildren }) => (
    <th className="px-3 py-2 text-left text-xs font-medium text-gray-700 dark:text-gray-300 border-r border-gray-300 dark:border-gray-600 last:border-r-0">
      {thChildren}
    </th>
  ),
  td: ({ children: tdChildren }) => (
    <td className="px-3 py-2 text-xs text-gray-600 dark:text-gray-400 border-r border-gray-300 dark:border-gray-600 last:border-r-0">
      {tdChildren}
    </td>
  ),
  h1: ({ children: h1Children }) => (
    <h1 className="text-xl font-bold mb-4 mt-6 text-gray-900 dark:text-gray-100 border-b border-gray-200 dark:border-gray-700 pb-2 last:mb-0 last:pb-0">
      {h1Children}
    </h1>
  ),
  h2: ({ children: h2Children }) => (
    <h2 className="text-lg font-semibold mb-3 mt-5 text-gray-900 dark:text-gray-100 last:mb-0">
      {h2Children}
    </h2>
  ),
  h3: ({ children: h3Children }) => (
    <h3 className="text-base font-semibold mb-2 mt-4 text-gray-800 dark:text-gray-200 last:mb-0">
      {h3Children}
    </h3>
  ),
  h4: ({ children: h4Children }) => (
    <h4 className="text-sm font-medium mb-2 mt-3 text-gray-700 dark:text-gray-300 last:mb-0">
      {h4Children}
    </h4>
  ),
  ul: ({ children: ulChildren }) => (
    <ul className="mb-3 pl-0 space-y-1 text-gray-800 dark:text-gray-200 last:mb-0">
      {ulChildren}
    </ul>
  ),
  ol: ({ children: olChildren }) => (
    <ol className="mb-3 pl-0 space-y-1 text-gray-800 dark:text-gray-200 last:mb-0">
      {olChildren}
    </ol>
  ),
  li: ({ children: liChildren }) => (
    <li className="flex items-start ml-4">
      <span className="mr-2 text-gray-500 dark:text-gray-400 select-none">
        •
      </span>
      <span className="flex-1">{liChildren}</span>
    </li>
  ),
  p: ({ children: pChildren }) => (
    <p className="mb-3 text-gray-800 dark:text-gray-200 leading-relaxed last:mb-0">
      {pChildren}
    </p>
  ),
  strong: ({ children: strongChildren }) => (
    <strong className="font-semibold text-gray-900 dark:text-gray-100">
      {strongChildren}
    </strong>
  ),
  blockquote: ({ children: blockquoteChildren }) => (
    <blockquote className="border-l-4 border-gray-300 dark:border-gray-600 pl-4 italic mb-3 text-gray-700 dark:text-gray-300 last:mb-0">
      {blockquoteChildren}
    </blockquote>
  ),
};

export { MarkdownContainer };
