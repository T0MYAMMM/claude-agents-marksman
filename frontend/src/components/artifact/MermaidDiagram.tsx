"use client";

import { useEffect, useId, useRef, useState } from "react";
import { useTheme } from "next-themes";
import mermaid from "mermaid";

interface MermaidDiagramProps {
  /** Raw mermaid source (the contents of a ```mermaid fenced block). */
  chart: string;
}

/**
 * Renders a mermaid source string as an inline SVG. Theme-aware via next-themes
 * (re-renders on light/dark flip) and degrades to the raw source in a <pre> if
 * the diagram fails to parse.
 */
export function MermaidDiagram({ chart }: MermaidDiagramProps) {
  const { resolvedTheme } = useTheme();
  const reactId = useId();
  // mermaid ids must be valid CSS selectors — strip the colons React injects.
  const renderId = `mermaid-${reactId.replace(/[:]/g, "")}`;
  const containerRef = useRef<HTMLDivElement>(null);
  const [svg, setSvg] = useState<string | null>(null);
  const [error, setError] = useState(false);

  useEffect(() => {
    let cancelled = false;
    const source = chart.trim();

    mermaid.initialize({
      startOnLoad: false,
      securityLevel: "strict",
      theme: resolvedTheme === "dark" ? "dark" : "neutral",
      fontFamily: "inherit",
    });

    mermaid
      .render(renderId, source)
      .then(({ svg: rendered }) => {
        if (!cancelled) {
          setSvg(rendered);
          setError(false);
        }
      })
      .catch(() => {
        if (!cancelled) {
          setSvg(null);
          setError(true);
        }
        // mermaid leaves an orphan error node on the body; clean it up.
        document.getElementById(renderId)?.remove();
      });

    return () => {
      cancelled = true;
    };
  }, [chart, resolvedTheme, renderId]);

  if (error) {
    return (
      <pre className="my-4 overflow-x-auto rounded-lg border border-border bg-card p-4 text-sm">
        <code>{chart}</code>
      </pre>
    );
  }

  return (
    <div
      ref={containerRef}
      className="my-4 flex justify-center overflow-x-auto rounded-lg border border-border bg-card p-4"
      // SVG comes from mermaid's own renderer (securityLevel: strict sanitizes it).
      dangerouslySetInnerHTML={svg ? { __html: svg } : undefined}
    />
  );
}
