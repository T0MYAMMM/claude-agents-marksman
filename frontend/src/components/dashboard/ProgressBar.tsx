import { cn } from "@/lib/utils";

/** Slim progress track with a brand fill; turns success-green when complete. */
export function ProgressBar({ value }: { value: number }) {
  const pct = Math.max(0, Math.min(100, value));
  const done = pct >= 100;
  return (
    <div className="w-full">
      <div className="h-2 w-full overflow-hidden rounded-full bg-muted">
        <div
          className={cn(
            "h-full rounded-full transition-[width] duration-300 ease-[cubic-bezier(0.22,1,0.36,1)]",
            done ? "bg-state-success" : "bg-brand",
          )}
          style={{ width: `${pct}%` }}
          role="progressbar"
          aria-valuenow={pct}
          aria-valuemin={0}
          aria-valuemax={100}
        />
      </div>
      <span className="mt-1 block text-right text-xs text-muted-foreground">
        {pct}%
      </span>
    </div>
  );
}
