import * as React from "react";
import type { LucideIcon } from "lucide-react";

import { cn } from "@/lib/utils";

interface EmptyStateProps {
  icon: LucideIcon;
  title: string;
  description?: string;
  action?: React.ReactNode;
  /** Compact inline variant (smaller padding, no min-height). */
  compact?: boolean;
  /** Destructive tint for error states. */
  destructive?: boolean;
  className?: string;
}

/** Centered empty/error placeholder: icon + title + description + optional action. */
export function EmptyState({
  icon: Icon,
  title,
  description,
  action,
  compact = false,
  destructive = false,
  className,
}: EmptyStateProps) {
  return (
    <div
      className={cn(
        "flex flex-col items-center justify-center rounded-xl border border-dashed border-border text-center",
        compact ? "gap-2 px-4 py-6" : "gap-3 px-6 py-12",
        className,
      )}
    >
      <span
        className={cn(
          "flex items-center justify-center rounded-full",
          compact ? "size-9" : "size-12",
          destructive
            ? "bg-destructive/10 text-destructive"
            : "bg-muted text-muted-foreground",
        )}
      >
        <Icon className={compact ? "size-4" : "size-5"} />
      </span>
      <div className="space-y-1">
        <p
          className={cn(
            "font-display font-semibold",
            compact ? "text-sm" : "text-base",
          )}
        >
          {title}
        </p>
        {description && (
          <p className="mx-auto max-w-sm text-sm text-muted-foreground">
            {description}
          </p>
        )}
      </div>
      {action}
    </div>
  );
}
