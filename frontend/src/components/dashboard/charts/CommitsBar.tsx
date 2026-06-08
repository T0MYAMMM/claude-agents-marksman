"use client";

import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import type { CommitsByType } from "@/types";
import { useChartTheme } from "./use-chart-theme";
import { ChartTooltip } from "./ChartTooltip";

/** Commits grouped by type as a compact bar chart. */
export function CommitsBar({ data }: { data: CommitsByType[] }) {
  const theme = useChartTheme();

  return (
    <ResponsiveContainer width="100%" height={220}>
      <BarChart data={data} margin={{ top: 8, right: 8, bottom: 0, left: -16 }}>
        <CartesianGrid
          strokeDasharray="3 3"
          stroke={theme.border}
          vertical={false}
        />
        <XAxis
          dataKey="type"
          tick={{ fill: theme.mutedForeground, fontSize: 11 }}
          tickLine={false}
          axisLine={{ stroke: theme.border }}
        />
        <YAxis
          allowDecimals={false}
          tick={{ fill: theme.mutedForeground, fontSize: 11 }}
          tickLine={false}
          axisLine={false}
          width={32}
        />
        <Tooltip
          cursor={{ fill: theme.border, opacity: 0.3 }}
          content={(props) => (
            <ChartTooltip {...props} theme={theme} nameKey="type" />
          )}
        />
        <Bar dataKey="count" name="Commits" radius={[4, 4, 0, 0]}>
          {data.map((_, i) => (
            <Cell key={i} fill={theme.palette[i % theme.palette.length]} />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}
