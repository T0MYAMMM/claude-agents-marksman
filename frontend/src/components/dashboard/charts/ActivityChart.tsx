"use client";

import {
  Area,
  AreaChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import type { ActivityPoint } from "@/types";
import { useChartTheme } from "./use-chart-theme";
import { ChartTooltip } from "./ChartTooltip";

/** Format an ISO date (YYYY-MM-DD) as a short "Jun 1" tick. */
function shortDate(iso: string): string {
  const d = new Date(`${iso}T00:00:00`);
  if (Number.isNaN(d.getTime())) return iso;
  return d.toLocaleDateString(undefined, { month: "short", day: "numeric" });
}

/** 14-day commit activity as a soft terracotta area chart. */
export function ActivityChart({ data }: { data: ActivityPoint[] }) {
  const theme = useChartTheme();

  return (
    <ResponsiveContainer width="100%" height={220}>
      <AreaChart data={data} margin={{ top: 8, right: 8, bottom: 0, left: -16 }}>
        <defs>
          <linearGradient id="activityFill" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor={theme.brand} stopOpacity={0.35} />
            <stop offset="100%" stopColor={theme.brand} stopOpacity={0.02} />
          </linearGradient>
        </defs>
        <CartesianGrid
          strokeDasharray="3 3"
          stroke={theme.border}
          vertical={false}
        />
        <XAxis
          dataKey="date"
          tickFormatter={shortDate}
          tick={{ fill: theme.mutedForeground, fontSize: 11 }}
          tickLine={false}
          axisLine={{ stroke: theme.border }}
          minTickGap={16}
        />
        <YAxis
          allowDecimals={false}
          tick={{ fill: theme.mutedForeground, fontSize: 11 }}
          tickLine={false}
          axisLine={false}
          width={32}
        />
        <Tooltip
          cursor={{ stroke: theme.border }}
          content={(props) => (
            <ChartTooltip
              {...props}
              theme={theme}
              label={
                props.label !== undefined ? shortDate(String(props.label)) : undefined
              }
            />
          )}
        />
        <Area
          type="monotone"
          dataKey="commits"
          name="Commits"
          stroke={theme.brand}
          strokeWidth={2}
          fill="url(#activityFill)"
          dot={false}
          activeDot={{ r: 4, fill: theme.brand }}
        />
      </AreaChart>
    </ResponsiveContainer>
  );
}
