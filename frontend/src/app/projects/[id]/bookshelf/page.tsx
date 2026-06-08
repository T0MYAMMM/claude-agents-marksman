import { ProjectShelf } from "@/components/bookshelf/ProjectShelf";

// Project-scoped bookshelf entry (alias of /bookshelf/[projectId]).
export default async function ProjectBookshelfPage({
  params,
}: {
  params: { id: string };
}) {
  return <ProjectShelf projectId={params.id} />;
}
