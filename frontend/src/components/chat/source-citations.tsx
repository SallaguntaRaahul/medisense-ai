"use client";

import { useState } from "react";
import { ChevronDown, ExternalLink } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import type { SourceChunk } from "@/lib/types";

export function SourceCitations({ sources }: { sources: SourceChunk[] }) {
  const [expanded, setExpanded] = useState<string | null>(null);

  if (!sources.length) return null;

  const uniqueByTopic = Array.from(new Map(sources.map((s) => [s.topic, s])).values());

  return (
    <div className="mt-2 flex flex-wrap gap-1.5">
      {uniqueByTopic.map((source) => {
        const isOpen = expanded === source.topic;
        return (
          <div key={source.topic} className="w-full sm:w-auto">
            <button
              onClick={() => setExpanded(isOpen ? null : source.topic)}
              className="inline-flex items-center gap-1"
            >
              <Badge
                variant="secondary"
                className="cursor-pointer gap-1 font-normal hover:bg-accent hover:text-accent-foreground transition-colors"
              >
                {source.topic}
                <ChevronDown className={`h-3 w-3 transition-transform ${isOpen ? "rotate-180" : ""}`} />
              </Badge>
            </button>
            {isOpen && (
              <div className="mt-1.5 max-w-md rounded-md border bg-muted/50 p-2.5 text-xs text-muted-foreground">
                <p className="line-clamp-4">{source.text}</p>
                {source.url && (
                  <a
                    href={source.url}
                    target="_blank"
                    rel="noreferrer"
                    className="mt-1.5 inline-flex items-center gap-1 text-primary hover:underline"
                  >
                    MedlinePlus source <ExternalLink className="h-3 w-3" />
                  </a>
                )}
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
}
