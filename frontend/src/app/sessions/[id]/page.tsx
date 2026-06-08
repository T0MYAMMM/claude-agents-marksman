import { Hourglass, MessageSquare } from "lucide-react";

import { api } from "@/lib/api-client";
import { ProgressBar } from "@/components/dashboard/ProgressBar";
import { StateBadge } from "@/components/session/StateBadge";
import { FeedbackForm } from "@/components/session/FeedbackForm";
import { ApproveButton } from "@/components/session/ApproveButton";
import { CommitTimeline } from "@/components/history/CommitTimeline";
import { PageHeader } from "@/components/layout/PageHeader";
import { Badge } from "@/components/ui/badge";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { EmptyState } from "@/components/ui/empty-state";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Separator } from "@/components/ui/separator";

// Session/Topic Manager — current state, feedback injection, and commit history.
export default async function SessionPage({
  params,
}: {
  params: { id: string };
}) {
  const [session, page, feedback] = await Promise.all([
    api.getSession(params.id),
    api.listCommits(params.id),
    api.listFeedback(params.id),
  ]);

  // Project name for the breadcrumb (best-effort; tolerate failure).
  let projectName = "Project";
  try {
    projectName = (await api.getProject(session.project_id)).name;
  } catch {
    /* breadcrumb falls back to a generic label */
  }

  const awaitingReview = session.state === "WAITING_FOR_HUMAN";
  const openFeedback = feedback.filter((f) => !f.resolved);

  return (
    <div className="space-y-8">
      <div>
        <PageHeader
          crumbs={[
            { label: "Dashboard", href: "/" },
            { label: projectName, href: `/projects/${session.project_id}` },
            { label: session.title },
          ]}
          title={session.title}
          actions={<StateBadge state={session.state} />}
        />
        <div className="max-w-md">
          <ProgressBar value={session.progress_pct} />
        </div>
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        <Card className="min-w-0">
          <CardHeader>
            <CardTitle className="text-xs font-medium uppercase tracking-wide text-muted-foreground">
              Review &amp; Feedback
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            {awaitingReview ? (
              <div className="space-y-4">
                <FeedbackForm sessionId={session.id} />
                <Separator />
                <ApproveButton sessionId={session.id} enabled={awaitingReview} />
              </div>
            ) : (
              <EmptyState
                compact
                icon={Hourglass}
                title="Not awaiting review"
                description="Feedback can be injected when the state is WAITING FOR HUMAN."
              />
            )}

            {openFeedback.length > 0 && (
              <div className="space-y-2">
                <div className="flex items-center gap-2">
                  <span className="text-xs font-medium uppercase tracking-wide text-muted-foreground">
                    Open feedback
                  </span>
                  <Badge variant="outline">{openFeedback.length}</Badge>
                </div>
                <ul className="space-y-2">
                  {openFeedback.map((f) => (
                    <li
                      key={f.id}
                      className="flex items-start gap-2 rounded-md border bg-accent/40 px-3 py-2 text-sm"
                    >
                      <MessageSquare className="mt-0.5 size-4 shrink-0 text-muted-foreground" />
                      <span className="min-w-0 break-words">{f.comment}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </CardContent>
        </Card>

        <Card className="min-w-0">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-xs font-medium uppercase tracking-wide text-muted-foreground">
              Commit History
              <Badge variant="secondary">{page.items.length}</Badge>
            </CardTitle>
          </CardHeader>
          <CardContent className="min-w-0">
            <ScrollArea className="max-h-[60vh] w-full [&>[data-slot=scroll-area-viewport]>div]:!block">
              <div className="min-w-0 pr-3">
                <CommitTimeline commits={page.items} />
              </div>
            </ScrollArea>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
