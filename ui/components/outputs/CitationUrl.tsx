import React from "react";

export interface CitationUrlProps {
  url: string;
}

function CitationUrl({ url }: CitationUrlProps) {
  if (!url) {
    return (
      <span
        className="text-sm text-muted-foreground italic"
        aria-label="No citation URL provided"
      >
        No citation URL
      </span>
    );
  }

  return (
    <a
      href={url}
      target="_blank"
      rel="noopener noreferrer"
      className="text-sm underline underline-offset-4 text-primary hover:text-primary/80 focus:outline-none focus:ring-2 focus:ring-ring rounded-sm"
      aria-label={`Citation source: ${url}`}
    >
      {url}
    </a>
  );
}

export { CitationUrl };
