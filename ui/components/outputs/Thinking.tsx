import { ChevronDown, ChevronUp, Sparkles } from "lucide-react";
import { useState } from "react";

interface ThinkingProps {
  reasoningContent: string;
  initiallyOpen?: boolean;
  className?: string;
}

function Thinking({ reasoningContent, initiallyOpen = false }: ThinkingProps) {
  const [open, setOpen] = useState(initiallyOpen);

  if (!reasoningContent || reasoningContent.trim() === "") {
    return null;
  }

  const paragraphs = reasoningContent
    .split(/\n\n+/)
    .map((p) => p.trim())
    .filter((p) => p.length > 0);

  return (
    <div className={"text-sm"}>
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
            className="mr-4 w-px bg-neutral-400/40 rounded-sm"
          />
          <div className="flex-1 space-y-3">
            {paragraphs.map((para, idx) => (
              <p key={idx} className="leading-relaxed whitespace-pre-wrap">
                {para}
              </p>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

export { Thinking };
