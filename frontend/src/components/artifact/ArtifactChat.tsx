"use client";

import { useRef, useState } from "react";
import { Check, Loader2, Send, Sparkles, X } from "lucide-react";
import { toast } from "sonner";

import { chatAction, saveArtifactAction } from "@/app/artifacts/[fileId]/actions";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { cn } from "@/lib/utils";
import type { ChatMessage } from "@/types";

interface Props {
  fileId: string;
  currentMarkdown: string;
  onApplied: (markdown: string) => void;
}

/** Claude-powered side panel that helps edit the open Markdown document. */
export function ArtifactChat({ fileId, currentMarkdown, onApplied }: Props) {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [pending, setPending] = useState(false);
  const [saving, setSaving] = useState(false);
  const [revision, setRevision] = useState<string | null>(null);
  const [notConfigured, setNotConfigured] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);

  async function send() {
    const text = input.trim();
    if (!text || pending) return;
    const next = [...messages, { role: "user" as const, content: text }];
    setMessages(next);
    setInput("");
    setPending(true);
    try {
      const res = await chatAction(fileId, next, currentMarkdown);
      setMessages((m) => [
        ...m,
        { role: "assistant", content: res.reply || "I've prepared an update below." },
      ]);
      if (res.revised_markdown) setRevision(res.revised_markdown);
    } catch (err) {
      const msg = err instanceof Error ? err.message : String(err);
      if (msg.includes("503") || msg.toLowerCase().includes("not configured")) {
        setNotConfigured(true);
      } else {
        toast.error("Assistant request failed", { description: msg.slice(0, 160) });
        setMessages((m) => [...m, { role: "assistant", content: "⚠️ Request failed." }]);
      }
    } finally {
      setPending(false);
      requestAnimationFrame(() =>
        scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight }),
      );
    }
  }

  async function apply() {
    if (!revision) return;
    setSaving(true);
    try {
      await saveArtifactAction(fileId, revision);
      onApplied(revision);
      toast.success("Saved to Google Drive");
      setMessages((m) => [...m, { role: "assistant", content: "✅ Applied and saved." }]);
      setRevision(null);
    } catch (err) {
      const msg = err instanceof Error ? err.message : String(err);
      toast.error("Save failed", { description: msg.slice(0, 160) });
    } finally {
      setSaving(false);
    }
  }

  if (notConfigured) {
    return (
      <div className="flex h-full flex-col items-center justify-center gap-2 p-6 text-center">
        <Sparkles className="size-6 text-muted-foreground" />
        <p className="text-sm font-medium">Assistant not configured</p>
        <p className="text-xs text-muted-foreground">
          Set <code className="rounded bg-muted px-1">APP_ANTHROPIC_API_KEY</code> on the
          backend to enable the editing assistant.
        </p>
      </div>
    );
  }

  return (
    <div className="flex h-full min-h-0 flex-col">
      <div className="flex items-center gap-2 border-b px-4 py-3">
        <Sparkles className="size-4 text-brand" />
        <span className="font-display text-sm font-semibold">Edit assistant</span>
      </div>

      <div ref={scrollRef} className="min-h-0 flex-1 overflow-y-auto">
        <div className="space-y-3 p-4">
          {messages.length === 0 && (
            <p className="text-xs text-muted-foreground">
              Ask for changes to this document — e.g. “add a troubleshooting section” or
              “tighten the overview”. I’ll propose a revision you can save to Drive.
            </p>
          )}
          {messages.map((m, i) => (
            <div
              key={i}
              className={cn(
                "max-w-[90%] rounded-lg px-3 py-2 text-sm break-words",
                m.role === "user"
                  ? "ml-auto bg-brand/15 text-foreground"
                  : "bg-muted text-foreground",
              )}
            >
              {m.content}
            </div>
          ))}
          {pending && (
            <div className="flex items-center gap-2 text-xs text-muted-foreground">
              <Loader2 className="size-3 animate-spin" /> thinking…
            </div>
          )}
        </div>
      </div>

      {revision && (
        <div className="flex items-center justify-between gap-2 border-t bg-accent/40 px-4 py-2">
          <span className="text-xs text-muted-foreground">Revision ready</span>
          <div className="flex gap-1.5">
            <Button size="sm" variant="ghost" onClick={() => setRevision(null)} disabled={saving}>
              <X className="size-3.5" /> Dismiss
            </Button>
            <Button size="sm" variant="brand" onClick={apply} disabled={saving}>
              {saving ? <Loader2 className="size-3.5 animate-spin" /> : <Check className="size-3.5" />}
              Apply &amp; save
            </Button>
          </div>
        </div>
      )}

      <div className="flex items-end gap-2 border-t p-3">
        <Textarea
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter" && !e.shiftKey) {
              e.preventDefault();
              void send();
            }
          }}
          rows={2}
          placeholder="Ask for an edit…"
          className="max-h-32 min-h-0 resize-none"
          disabled={pending}
        />
        <Button size="icon" variant="brand" onClick={() => void send()} disabled={pending || !input.trim()}>
          <Send className="size-4" />
          <span className="sr-only">Send</span>
        </Button>
      </div>
    </div>
  );
}
