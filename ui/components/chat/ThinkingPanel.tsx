import { ChevronDown, ChevronUp, Sparkles } from "lucide-react";
import { useState } from "react";

import { MarkdownContainer } from "../MarkdownContainer";

interface ThinkingPanelProps {
  reasoningContent: string;
  initiallyOpen?: boolean;
  className?: string;
}

function ThinkingPanel({
  reasoningContent,
  initiallyOpen = false,
  className = "",
}: ThinkingPanelProps) {
  const [open, setOpen] = useState(initiallyOpen);

  if (!reasoningContent || reasoningContent.trim() === "") {
    return null;
  }

  return (
    <div className={`text-sm ${className} mb-4`}>
      <button
        type="button"
        role="button"
        onClick={() => setOpen((o) => !o)}
        className="flex items-center gap-1 py-2 text-left hover:cursor-pointer hover:opacity-90 transition-colors focus:outline-none active:opacity-80"
        aria-expanded={open}
        aria-controls="thinking-panel-content"
      >
        <Sparkles className="h-4 w-4 text-primary" aria-hidden="true" />
        <span className="font-medium select-none">
          {open ? "Hide thinking" : "Show thinking"}
        </span>
        {open ? (
          <ChevronUp className="h-4 w-4 opacity-70" aria-hidden="true" />
        ) : (
          <ChevronDown className="h-4 w-4 opacity-70" aria-hidden="true" />
        )}
      </button>
      {open && (
        <div className="flex pb-3 pt-1 pr-3" id="thinking-panel-content">
          <div
            aria-hidden="true"
            className="w-px bg-neutral-400/40 rounded-sm"
          />
          <div className="flex-1">
            <MarkdownContainer>{reasoningContent}</MarkdownContainer>
          </div>
        </div>
      )}
    </div>
  );
}

export { ThinkingPanel };
