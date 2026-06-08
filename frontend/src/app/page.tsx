import {
  Activity,
  Bot,
  FileText,
  FolderGit2,
  GitCommitHorizontal,
  Workflow,
  WifiOff,
} from "lucide-react";

import { api } from "@/lib/api-client";
import { PageHeader } from "@/components/layout/PageHeader";
import { StatTile } from "@/components/dashboard/StatTile";
import { RecentSessions } from "@/components/dashboard/RecentSessions";
import { ActivityChart } from "@/components/dashboard/charts/ActivityChart";
import { SessionsDonut } from "@/components/dashboard/charts/SessionsDonut";
import { CommitsBar } from "@/components/dashboard/charts/CommitsBar";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { EmptyState } from "@/components/ui/empty-state";

// Dashboard — system-wide overview: metric tiles, charts, recent activity.
export default async function DashboardPage() {
  let stats;
  try {
    stats = await api.getOverview();
  } catch {
    return (
      <>
        <PageHeader crumbs={[{ label: "Dashboard" }]} title="Dashboard" />
        <EmptyState
          icon={WifiOff}
          destructive
          title="Could not load overview metrics"
          description="The stats endpoint is unreachable. Is the backend running and reachable over Tailscale?"
        />
      </>
    );
  }

  const { totals } = stats;

  return (
    <>
      <PageHeader
        crumbs={[{ label: "Dashboard" }]}
        title="Dashboard"
        description="A live overview of every project, session, agent, and commit in the system."
      />

      {/* Metric tiles */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-5">
        <StatTile label="Projects" value={totals.projects} icon={FolderGit2} />
        <StatTile label="Sessions" value={totals.sessions} icon={Workflow} />
        <StatTile label="Agents" value={totals.agents} icon={Bot} />
        <StatTile
          label="Commits"
          value={totals.commits}
          icon={GitCommitHorizontal}
        />
        <StatTile label="Documents" value={totals.documents} icon={FileText} />
      </div>

      {/* Charts */}
      <div className="mt-6 grid gap-4 lg:grid-cols-3">
        <Card className="card-lift py-5 lg:col-span-2">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 font-display text-lg">
              <Activity className="size-4 text-brand" />
              Commit activity
            </CardTitle>
            <p className="text-sm text-muted-foreground">Last 14 days</p>
          </CardHeader>
          <CardContent>
            <ActivityChart data={stats.activity} />
          </CardContent>
        </Card>

        <Card className="card-lift py-5">
          <CardHeader>
            <CardTitle className="font-display text-lg">
              Sessions by state
            </CardTitle>
          </CardHeader>
          <CardContent>
            {stats.sessions_by_state.length > 0 ? (
              <SessionsDonut data={stats.sessions_by_state} />
            ) : (
              <EmptyState
                icon={Workflow}
                compact
                title="No sessions yet"
              />
            )}
          </CardContent>
        </Card>
      </div>

      {/* Commits by type + recent activity */}
      <div className="mt-4 grid gap-4 lg:grid-cols-3">
        <Card className="card-lift py-5">
          <CardHeader>
            <CardTitle className="font-display text-lg">
              Commits by type
            </CardTitle>
          </CardHeader>
          <CardContent>
            {stats.commits_by_type.length > 0 ? (
              <CommitsBar data={stats.commits_by_type} />
            ) : (
              <EmptyState
                icon={GitCommitHorizontal}
                compact
                title="No commits yet"
              />
            )}
          </CardContent>
        </Card>

        <Card className="card-lift py-5 lg:col-span-2">
          <CardHeader>
            <CardTitle className="font-display text-lg">
              Recent activity
            </CardTitle>
            <p className="text-sm text-muted-foreground">Latest sessions</p>
          </CardHeader>
          <CardContent>
            <RecentSessions sessions={stats.recent_sessions} />
          </CardContent>
        </Card>
      </div>
    </>
  );
}
