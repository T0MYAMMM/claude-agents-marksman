"use client";

import { useState } from "react";
import { MessageSquareText, X } from "lucide-react";

import { MarkdownRenderer } from "@/components/artifact/MarkdownRenderer";
import { ArtifactChat } from "@/components/artifact/ArtifactChat";
import { Button } from "@/components/ui/button";

interface Props {
  fileId: string;
  initialContent: string;
}

/** Artifact viewer + collapsible AI editing panel; holds the live document state. */
export function ArtifactWorkspace({ fileId, initialContent }: Props) {
  const [content, setContent] = useState(initialContent);
  const [chatOpen, setChatOpen] = useState(false);

  return (
    <div className="relative flex flex-col gap-6 xl:flex-row">
      <div className="min-w-0 flex-1">
        <MarkdownRenderer key={content.length} content={content} />
      </div>

      {chatOpen ? (
        <aside className="h-[70vh] w-full shrink-0 overflow-hidden rounded-xl border bg-card xl:sticky xl:top-20 xl:h-[calc(100vh-7rem)] xl:w-[360px]">
          <div className="flex h-full flex-col">
            <div className="flex justify-end px-2 pt-2">
              <Button size="icon" variant="ghost" onClick={() => setChatOpen(false)}>
                <X className="size-4" />
                <span className="sr-only">Close assistant</span>
              </Button>
            </div>
            <div className="min-h-0 flex-1">
              <ArtifactChat fileId={fileId} currentMarkdown={content} onApplied={setContent} />
            </div>
          </div>
        </aside>
      ) : (
        <Button
          variant="brand"
          className="fixed right-6 bottom-6 z-20 shadow-[var(--shadow-lift)] xl:right-10"
          onClick={() => setChatOpen(true)}
        >
          <MessageSquareText className="size-4" />
          Edit with AI
        </Button>
      )}
    </div>
  );
}
