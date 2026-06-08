import Link from "next/link";
import { FileText } from "lucide-react";

import type { Document } from "@/types";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { EmptyState } from "@/components/ui/empty-state";
import { bookTitle, type CategoryMeta } from "@/components/bookshelf/categories";

interface ShelfProps {
  meta: CategoryMeta;
  documents: Document[];
}

/** One category "shelf": header row, a grid of book-spine cards, and a shelf board. */
export function Shelf({ meta, documents }: ShelfProps) {
  const Icon = meta.icon;
  return (
    <section id={meta.key} className="scroll-mt-20 space-y-3">
      <div className="flex items-center gap-2">
        <Icon className="size-4 text-brand" />
        <h2 className="font-display text-lg">{meta.label}</h2>
        <Badge variant="secondary">{documents.length}</Badge>
      </div>

      {documents.length === 0 ? (
        <EmptyState
          compact
          icon={Icon}
          title={`No documents in ${meta.label.toLowerCase()} yet`}
        />
      ) : (
        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
          {documents.map((doc) => (
            <Link
              key={doc.gdrive_file_id}
              href={`/artifacts/${doc.gdrive_file_id}?from=bookshelf`}
              className="group block"
            >
              <Card className="card-lift gap-2 border-l-4 border-l-brand/60 py-4 transition-all duration-300 ease-[cubic-bezier(0.22,1,0.36,1)] group-hover:-translate-y-1 group-hover:border-brand/40 group-hover:border-l-brand group-hover:shadow-[var(--shadow-lift)]">
                <CardHeader>
                  <CardTitle className="font-display text-base leading-snug">
                    {bookTitle(doc.file_name)}
                  </CardTitle>
                </CardHeader>
                <CardContent className="flex items-center gap-1.5 text-xs text-muted-foreground">
                  <FileText className="size-3.5" />
                  <span>{new Date(doc.created_at).toLocaleDateString()}</span>
                </CardContent>
              </Card>
            </Link>
          ))}
        </div>
      )}

      {/* Shelf board — physical "library" cue. */}
      <div className="h-0.5 w-full rounded-full bg-gradient-to-r from-border to-transparent shadow-[var(--shadow-soft)]" />
    </section>
  );
}
