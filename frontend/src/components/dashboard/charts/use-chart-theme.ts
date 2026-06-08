"use client";

import { useEffect, useState } from "react";
import { useTheme } from "next-themes";

export interface ChartTheme {
  brand: string;
  mutedForeground: string;
  border: string;
  card: string;
  foreground: string;
  /** A small token-driven palette for categorical series (donut/bar slices). */
  palette: string[];
}

const FALLBACK: ChartTheme = {
  brand: "#c1583a",
  mutedForeground: "#7a756e",
  border: "#e3ddd4",
  card: "#ffffff",
  foreground: "#2b2722",
  palette: ["#c1583a", "#5b86c4", "#4fa06b", "#d9a441", "#8a7fb5", "#9a9690"],
};

/** Resolve a CSS custom property to a concrete color string off a probe element. */
function readVar(probe: HTMLElement, name: string, fallback: string): string {
  const raw = getComputedStyle(probe).getPropertyValue(name).trim();
  return raw || fallback;
}

/**
 * Reads the warm-editorial OKLCH CSS vars into concrete colors recharts can use.
 * Re-resolves whenever the next-themes theme flips (light/dark aware).
 */
export function useChartTheme(): ChartTheme {
  const { resolvedTheme } = useTheme();
  const [theme, setTheme] = useState<ChartTheme>(FALLBACK);

  useEffect(() => {
    const probe = document.createElement("span");
    probe.style.display = "none";
    document.body.appendChild(probe);

    const brand = readVar(probe, "--brand", FALLBACK.brand);
    const next: ChartTheme = {
      brand,
      mutedForeground: readVar(
        probe,
        "--muted-foreground",
        FALLBACK.mutedForeground,
      ),
      border: readVar(probe, "--border", FALLBACK.border),
      card: readVar(probe, "--card", FALLBACK.card),
      foreground: readVar(probe, "--foreground", FALLBACK.foreground),
      palette: [
        brand,
        readVar(probe, "--state-info", FALLBACK.palette[1]),
        readVar(probe, "--state-success", FALLBACK.palette[2]),
        readVar(probe, "--state-warning", FALLBACK.palette[3]),
        readVar(probe, "--accent-foreground", FALLBACK.palette[4]),
        readVar(probe, "--muted-foreground", FALLBACK.palette[5]),
      ],
    };

    document.body.removeChild(probe);
    setTheme(next);
  }, [resolvedTheme]);

  return theme;
}
