"use client";

import type { ChartTheme } from "./use-chart-theme";

type TooltipValue = string | number | readonly (string | number)[];

interface TooltipPayloadEntry {
  name?: string | number;
  value?: TooltipValue;
  color?: string;
  payload?: Record<string, unknown>;
}

interface ChartTooltipProps {
  active?: boolean;
  payload?: readonly TooltipPayloadEntry[];
  label?: string | number;
  theme: ChartTheme;
  /** Optional override for the row label (defaults to the series name). */
  nameKey?: string;
}

/** Clean, token-styled tooltip shared by the dashboard charts. */
export function ChartTooltip({
  active,
  payload,
  label,
  theme,
  nameKey,
}: ChartTooltipProps) {
  if (!active || !payload || payload.length === 0) return null;

  return (
    <div
      className="rounded-md border bg-card px-3 py-2 text-xs shadow-[var(--shadow-soft)]"
      style={{ borderColor: theme.border }}
    >
      {label !== undefined && (
        <p className="mb-1 font-medium text-foreground">{String(label)}</p>
      )}
      {payload.map((entry, i) => {
        const rowLabel =
          nameKey && entry.payload
            ? String(entry.payload[nameKey])
            : String(entry.name ?? "");
        return (
          <div key={i} className="flex items-center gap-2">
            <span
              className="inline-block size-2 rounded-[2px]"
              style={{ backgroundColor: entry.color ?? theme.brand }}
            />
            <span className="text-muted-foreground">{rowLabel}</span>
            <span className="ml-auto font-medium text-foreground">
              {String(entry.value)}
            </span>
          </div>
        );
      })}
    </div>
  );
}
