import type { ComponentPropsWithoutRef } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import rehypeHighlight from "rehype-highlight";
import rehypeSlug from "rehype-slug";

import { ScrollArea } from "@/components/ui/scroll-area";
import { MermaidDiagram } from "@/components/artifact/MermaidDiagram";

interface TocEntry {
  depth: number;
  text: string;
  slug: string;
}

function slugify(text: string): string {
  return text
    .toLowerCase()
    .replace(/[^a-z0-9\s-]/g, "")
    .trim()
    .replace(/\s+/g, "-");
}

/** Extract a simple Table of Contents from ATX headings (## / ###). */
function buildToc(markdown: string): TocEntry[] {
  const toc: TocEntry[] = [];
  for (const line of markdown.split("\n")) {
    const match = /^(#{1,3})\s+(.*)$/.exec(line);
    if (match) {
      const text = match[2].trim();
      toc.push({ depth: match[1].length, text, slug: slugify(text) });
    }
  }
  return toc;
}

/** True when a markdown code node carries the `mermaid` fence language. */
function isMermaidNode(node: unknown): boolean {
  const properties = (node as { properties?: { className?: unknown } })
    ?.properties;
  const className = properties?.className;
  const classes = Array.isArray(className)
    ? className
    : typeof className === "string"
      ? className.split(/\s+/)
      : [];
  return classes.includes("language-mermaid");
}

/**
 * Code-block override: fenced ```mermaid blocks render as a diagram (client
 * leaf); every other code block keeps the rehype-highlight output untouched.
 */
function CodeBlock({
  className,
  children,
  node,
  ...props
}: ComponentPropsWithoutRef<"code"> & { node?: unknown }) {
  if (/\blanguage-mermaid\b/.test(className ?? "")) {
    return <MermaidDiagram chart={String(children)} />;
  }
  return (
    <code className={className} {...props}>
      {children}
    </code>
  );
}

/**
 * Pre override: a mermaid block must not sit inside a styled <pre>, so we unwrap
 * it and let CodeBlock emit the diagram directly. All other blocks render a
 * normal <pre>.
 */
function PreBlock({
  children,
  node,
  ...props
}: ComponentPropsWithoutRef<"pre"> & {
  node?: { children?: unknown[] };
}) {
  const child = node?.children?.[0];
  if (isMermaidNode(child)) {
    return <>{children}</>;
  }
  return <pre {...props}>{children}</pre>;
}

export function MarkdownRenderer({ content }: { content: string }) {
  const toc = buildToc(content);
  return (
    <div className="grid gap-8 lg:grid-cols-[240px_1fr]">
      {toc.length > 0 && (
        <nav className="hidden lg:block">
          <div className="sticky top-20">
            <p className="mb-2 text-xs font-medium uppercase tracking-wide text-muted-foreground">
              Contents
            </p>
            <ScrollArea className="max-h-[calc(100vh-8rem)]">
              <ul className="space-y-1 pr-3 text-sm">
                {toc.map((e, i) => (
                  <li key={i} style={{ paddingLeft: `${(e.depth - 1) * 12}px` }}>
                    <a
                      href={`#${e.slug}`}
                      className="text-muted-foreground transition-colors hover:text-brand"
                    >
                      {e.text}
                    </a>
                  </li>
                ))}
              </ul>
            </ScrollArea>
          </div>
        </nav>
      )}
      <article className="prose-md min-w-0">
        <ReactMarkdown
          remarkPlugins={[remarkGfm]}
          rehypePlugins={[rehypeSlug, rehypeHighlight]}
          components={{ code: CodeBlock, pre: PreBlock }}
        >
          {content}
        </ReactMarkdown>
      </article>
    </div>
  );
}
