import Link from "next/link";
import { Inbox } from "lucide-react";

import type { RecentSession } from "@/types";
import { ProgressBar } from "@/components/dashboard/ProgressBar";
import { StateBadge } from "@/components/session/StateBadge";
import { EmptyState } from "@/components/ui/empty-state";

/** Recent sessions list: state badge + progress + deep link to the session. */
export function RecentSessions({ sessions }: { sessions: RecentSession[] }) {
  if (sessions.length === 0) {
    return (
      <EmptyState
        icon={Inbox}
        compact
        title="No recent sessions"
        description="Activity appears here as agents start working."
      />
    );
  }

  return (
    <ul className="divide-y divide-border">
      {sessions.map((s) => (
        <li key={s.id}>
          <Link
            href={`/sessions/${s.id}`}
            className="-mx-2 flex flex-col gap-2 rounded-md px-2 py-3 transition-colors hover:bg-accent/50 sm:flex-row sm:items-center sm:gap-4"
          >
            <div className="min-w-0 flex-1 space-y-1">
              <p className="truncate font-medium">{s.title}</p>
              <p className="text-xs text-muted-foreground">
                Started {new Date(s.started_at).toLocaleString()}
              </p>
            </div>
            <div className="flex items-center gap-3 sm:w-56">
              <StateBadge state={s.state} />
              <div className="flex-1">
                <ProgressBar value={s.progress_pct} />
              </div>
            </div>
          </Link>
        </li>
      ))}
    </ul>
  );
}
