import { LibraryBig } from "lucide-react";

import { api } from "@/lib/api-client";
import type { BookCategory, Document } from "@/types";
import { PageHeader } from "@/components/layout/PageHeader";
import { EmptyState } from "@/components/ui/empty-state";
import { CATEGORIES } from "@/components/bookshelf/categories";
import { Shelf } from "@/components/bookshelf/Shelf";

/**
 * Project-scoped library: 6 fixed shelves rendered from the backend library
 * contract. Server component — fetches via api-client (cache: no-store).
 */
export async function ProjectShelf({ projectId }: { projectId: string }) {
  const [project, library] = await Promise.all([
    api.getProject(projectId),
    api.listLibrary(projectId),
  ]);

  // Group documents by category, always exposing all 6 keys.
  const byCategory = Object.fromEntries(
    CATEGORIES.map((c) => [c.key, [] as Document[]]),
  ) as Record<BookCategory, Document[]>;

  for (const section of library.sections) {
    if (byCategory[section.category]) {
      byCategory[section.category].push(...section.documents);
    }
  }

  const total = Object.values(byCategory).reduce(
    (sum, docs) => sum + docs.length,
    0,
  );

  return (
    <>
      <PageHeader
        crumbs={[
          { label: "Bookshelf", href: "/bookshelf" },
          { label: project.name },
        ]}
        title={`${project.name} Library`}
        description="Browse the project's living documentation."
      />

      {total === 0 ? (
        <EmptyState
          icon={LibraryBig}
          title="This bookshelf is empty"
          description="Documents added to the project's Drive folder will appear here, sorted into categories."
        />
      ) : (
        <div className="space-y-8">
          {CATEGORIES.map((meta) => (
            <Shelf key={meta.key} meta={meta} documents={byCategory[meta.key]} />
          ))}
        </div>
      )}
    </>
  );
}
