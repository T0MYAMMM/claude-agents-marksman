"use client";

import { Cell, Pie, PieChart, ResponsiveContainer, Tooltip } from "recharts";

import type { SessionsByState } from "@/types";
import { useChartTheme } from "./use-chart-theme";
import { ChartTooltip } from "./ChartTooltip";

/** Sessions grouped by state as a token-driven donut. */
export function SessionsDonut({ data }: { data: SessionsByState[] }) {
  const theme = useChartTheme();
  const total = data.reduce((sum, d) => sum + d.count, 0);

  return (
    <div className="flex flex-col gap-4 sm:flex-row sm:items-center">
      <div className="relative h-[180px] w-full sm:w-[180px]">
        <ResponsiveContainer width="100%" height="100%">
          <PieChart>
            <Pie
              data={data}
              dataKey="count"
              nameKey="state"
              innerRadius={52}
              outerRadius={78}
              paddingAngle={2}
              stroke={theme.card}
              strokeWidth={2}
            >
              {data.map((_, i) => (
                <Cell
                  key={i}
                  fill={theme.palette[i % theme.palette.length]}
                />
              ))}
            </Pie>
            <Tooltip
              content={(props) => (
                <ChartTooltip {...props} theme={theme} nameKey="state" />
              )}
            />
          </PieChart>
        </ResponsiveContainer>
        <div className="pointer-events-none absolute inset-0 flex flex-col items-center justify-center">
          <span className="font-display text-2xl leading-none">{total}</span>
          <span className="text-xs text-muted-foreground">sessions</span>
        </div>
      </div>
      <ul className="grid flex-1 grid-cols-1 gap-1.5 text-sm">
        {data.map((d, i) => (
          <li key={d.state} className="flex items-center gap-2">
            <span
              className="inline-block size-2.5 rounded-[3px]"
              style={{ backgroundColor: theme.palette[i % theme.palette.length] }}
            />
            <span className="text-muted-foreground">
              {d.state.replace(/_/g, " ")}
            </span>
            <span className="ml-auto font-medium tabular-nums">{d.count}</span>
          </li>
        ))}
      </ul>
    </div>
  );
}
