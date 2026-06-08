import type { SessionState } from "@/types";
import { cn } from "@/lib/utils";

/** Token-driven pill colors per the 8-state mapping (terracotta reserved for REFINING). */
const STYLES: Record<SessionState, string> = {
  INIT: "bg-muted text-muted-foreground",
  PLANNING: "bg-state-info/15 text-state-info",
  WAITING_FOR_HUMAN: "bg-state-warning/20 text-state-warning",
  REFINING: "bg-brand/15 text-brand",
  EXECUTING: "bg-state-info/15 text-state-info",
  COMPLETED: "bg-state-success/15 text-state-success",
  FAILED: "bg-destructive/15 text-destructive",
  TERMINATED: "bg-muted text-muted-foreground line-through opacity-70",
};

export function StateBadge({ state }: { state: SessionState }) {
  return (
    <span
      className={cn(
        "inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium",
        STYLES[state],
      )}
    >
      {state.replace(/_/g, " ")}
    </span>
  );
}
