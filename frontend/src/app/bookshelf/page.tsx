import Link from "next/link";
import { FolderPlus, Library, WifiOff } from "lucide-react";

import { api } from "@/lib/api-client";
import { PageHeader } from "@/components/layout/PageHeader";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { EmptyState } from "@/components/ui/empty-state";

// Bookshelf entry — pick a project to browse its library.
export default async function BookshelfIndexPage() {
  let projects;
  try {
    projects = await api.listProjects();
  } catch {
    return (
      <>
        <PageHeader crumbs={[{ label: "Bookshelf" }]} title="Bookshelf" />
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
        crumbs={[{ label: "Bookshelf" }]}
        title="Bookshelf"
        description="Choose a project to browse its living documentation."
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
            <Link key={p.id} href={`/bookshelf/${p.id}`} className="group block">
              <Card className="card-lift gap-3 py-5 transition-all duration-300 ease-[cubic-bezier(0.22,1,0.36,1)] group-hover:-translate-y-1 group-hover:border-brand/40 group-hover:shadow-[var(--shadow-lift)]">
                <CardHeader className="flex-row items-center gap-2">
                  <Library className="size-4 text-brand" />
                  <CardTitle className="font-display text-lg">
                    {p.name}
                  </CardTitle>
                </CardHeader>
                {p.description && (
                  <CardContent className="line-clamp-2 text-sm text-muted-foreground">
                    {p.description}
                  </CardContent>
                )}
              </Card>
            </Link>
          ))}
        </div>
      )}
    </>
  );
}
