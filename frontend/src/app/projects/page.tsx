import { FolderPlus, WifiOff } from "lucide-react";

import { api } from "@/lib/api-client";
import { ProjectCard } from "@/components/dashboard/ProjectCard";
import { PageHeader } from "@/components/layout/PageHeader";
import { EmptyState } from "@/components/ui/empty-state";
import { Badge } from "@/components/ui/badge";

// Projects — grid overview of all registered projects.
export default async function ProjectsPage() {
  let projects;
  try {
    projects = await api.listProjects();
  } catch {
    return (
      <>
        <PageHeader
          crumbs={[{ label: "Projects" }]}
          title="Projects"
        />
        <EmptyState
          icon={WifiOff}
          destructive
          title="Could not reach the backend API"
          description="Is it running and reachable over Tailscale?"
        />
      </>
    );
  }

  return (
    <>
      <PageHeader
        crumbs={[{ label: "Projects" }]}
        title="Projects"
        description="Living workspaces tracked across plans, sessions, and artifacts."
        actions={<Badge variant="secondary">{projects.length} total</Badge>}
      />
      {projects.length === 0 ? (
        <EmptyState
          icon={FolderPlus}
          title="No projects yet"
          description="Projects appear here once registered with a Drive folder."
        />
      ) : (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {projects.map((p) => (
            <ProjectCard key={p.id} project={p} />
          ))}
        </div>
      )}
    </>
  );
}
