import { notFound } from "next/navigation";

import { api } from "@/lib/api-client";
import type { BookCategory, Document } from "@/types";
import { PageHeader } from "@/components/layout/PageHeader";
import { CATEGORIES } from "@/components/bookshelf/categories";
import { Shelf } from "@/components/bookshelf/Shelf";

// Deep view of a single category for direct linking.
export default async function BookshelfCategoryPage({
  params,
}: {
  params: { projectId: string; category: string };
}) {
  const meta = CATEGORIES.find((c) => c.key === params.category);
  if (!meta) notFound();

  const [project, library] = await Promise.all([
    api.getProject(params.projectId),
    api.listLibrary(params.projectId),
  ]);

  const documents: Document[] = library.sections
    .filter((s) => s.category === (params.category as BookCategory))
    .flatMap((s) => s.documents);

  return (
    <>
      <PageHeader
        crumbs={[
          { label: "Bookshelf", href: "/bookshelf" },
          { label: project.name, href: `/bookshelf/${params.projectId}` },
          { label: meta.label },
        ]}
        title={`${meta.label} — ${project.name}`}
        description="Browse the project's living documentation."
      />
      <Shelf meta={meta} documents={documents} />
    </>
  );
}
