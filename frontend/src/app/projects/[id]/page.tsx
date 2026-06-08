import Link from "next/link";
import { Bot } from "lucide-react";

import { api } from "@/lib/api-client";
import { ProgressBar } from "@/components/dashboard/ProgressBar";
import { StateBadge } from "@/components/session/StateBadge";
import { PageHeader } from "@/components/layout/PageHeader";
import { Badge } from "@/components/ui/badge";
import { Card } from "@/components/ui/card";
import { EmptyState } from "@/components/ui/empty-state";

// Project detail — lists the project's agent sessions.
export default async function ProjectPage({
  params,
}: {
  params: { id: string };
}) {
  const [project, sessions] = await Promise.all([
    api.getProject(params.id),
    api.listSessions(params.id),
  ]);

  return (
    <>
      <PageHeader
        crumbs={[
          { label: "Dashboard", href: "/" },
          { label: project.name },
        ]}
        title={project.name}
        description={project.description}
        actions={
          <Badge variant="secondary">
            {sessions.length} {sessions.length === 1 ? "session" : "sessions"}
          </Badge>
        }
      />

      <h2 className="mb-3 text-xs font-medium uppercase tracking-wide text-muted-foreground">
        Sessions
      </h2>
      {sessions.length === 0 ? (
        <EmptyState
          icon={Bot}
          title="No agent sessions yet"
          description="Sessions appear here once an agent begins working on this project."
        />
      ) : (
        <ul className="space-y-3">
          {sessions.map((s) => (
            <li key={s.id}>
              <Link href={`/sessions/${s.id}`} className="group block">
                <Card className="card-lift flex-row items-center gap-4 py-4 transition-all duration-300 ease-[cubic-bezier(0.22,1,0.36,1)] group-hover:-translate-y-1 group-hover:border-brand/40 group-hover:shadow-[var(--shadow-lift)]">
                  <div className="min-w-0 flex-1 px-2">
                    <div className="flex items-center gap-2">
                      <span className="truncate font-medium">{s.title}</span>
                      <StateBadge state={s.state} />
                    </div>
                    <p className="mt-1 text-xs text-muted-foreground">
                      started {new Date(s.started_at).toLocaleString()}
                    </p>
                  </div>
                  <div className="w-40 shrink-0 px-2">
                    <ProgressBar value={s.progress_pct} />
                  </div>
                </Card>
              </Link>
            </li>
          ))}
        </ul>
      )}
    </>
  );
}
