import { ProjectShelf } from "@/components/bookshelf/ProjectShelf";

// Project bookshelf — the 6 category shelves for one project.
export default async function BookshelfProjectPage({
  params,
}: {
  params: { projectId: string };
}) {
  return <ProjectShelf projectId={params.projectId} />;
}
