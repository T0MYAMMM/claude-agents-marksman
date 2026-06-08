import Link from "next/link";

import type { Commit, CommitType } from "@/types";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";

/** Dot color per commit type, brand-family tints. */
const DOT: Record<CommitType, string> = {
  PLAN: "bg-brand",
  REVISION: "bg-accent-foreground",
  STAGE_REPORT: "bg-muted-foreground",
  COMPLETION: "bg-[--color-state-success]",
  DOC: "bg-[--color-state-info]",
};

/** Count blockers recorded in a stage-report payload, defensively. */
function blockerCount(payload: Commit["payload"]): number {
  const blockers = payload?.blockers;
  return Array.isArray(blockers) ? blockers.length : 0;
}

/** Git-style chronological tree of agent actions for a session. */
export function CommitTimeline({ commits }: { commits: Commit[] }) {
  if (commits.length === 0) {
    return <p className="text-sm text-muted-foreground">No commits yet.</p>;
  }
  return (
    <ol className="relative border-l border-border pl-6">
      {commits.map((c) => {
        const blockers = blockerCount(c.payload);
        return (
          <li key={c.id} className="mb-6 min-w-0 last:mb-0">
            <span
              className={cn(
                "absolute -left-[5px] mt-1.5 size-2.5 rounded-full",
                DOT[c.type],
              )}
              aria-hidden
            />
            <div className="flex flex-wrap items-baseline gap-x-2 gap-y-0.5">
              <span className="font-mono text-xs text-muted-foreground">
                {c.type}
              </span>
              <time className="text-xs text-muted-foreground">
                {new Date(c.created_at).toLocaleString()}
              </time>
            </div>
            <p className="mt-1 text-sm break-words text-foreground">
              {c.message}
            </p>
            {blockers > 0 && (
              <Badge variant="destructive" className="mt-1.5">
                {blockers} blockers
              </Badge>
            )}
            {c.gdrive_ref_id && (
              <p className="mt-1.5 min-w-0">
                <Link
                  href={`/artifacts/${c.gdrive_ref_id}`}
                  className="inline-flex max-w-full items-baseline gap-1 font-mono text-xs text-brand hover:underline"
                >
                  <span className="shrink-0">artifact:</span>
                  <span className="truncate">{c.gdrive_ref_id}</span>
                </Link>
              </p>
            )}
          </li>
        );
      })}
    </ol>
  );
}
