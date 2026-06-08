import { FileWarning } from "lucide-react";

import { api } from "@/lib/api-client";
import { ArtifactWorkspace } from "@/components/artifact/ArtifactWorkspace";
import { PageHeader } from "@/components/layout/PageHeader";
import { Badge } from "@/components/ui/badge";
import { EmptyState } from "@/components/ui/empty-state";
import type { Crumb } from "@/components/layout/PageHeader";

// Artifact Viewer — renders a Markdown artifact fetched from Drive via the backend.
export default async function ArtifactPage({
  params,
  searchParams,
}: {
  params: { fileId: string };
  searchParams: { from?: string };
}) {
  const fromBookshelf = searchParams.from === "bookshelf";
  const crumbs: Crumb[] = fromBookshelf
    ? [
        { label: "Bookshelf", href: "/bookshelf" },
        { label: "Artifact" },
      ]
    : [{ label: "Dashboard", href: "/" }, { label: "Artifact" }];

  let artifact;
  try {
    artifact = await api.getArtifact(params.fileId);
  } catch {
    return (
      <>
        <PageHeader crumbs={crumbs} title="Artifact" />
        <EmptyState
          icon={FileWarning}
          destructive
          title="Could not load artifact"
          description={`Could not load artifact ${params.fileId} from Google Drive.`}
        />
      </>
    );
  }

  return (
    <>
      <PageHeader
        crumbs={crumbs}
        title="Artifact"
        actions={
          <Badge variant="outline" className="font-mono">
            {artifact.gdrive_file_id}
          </Badge>
        }
      />
      <ArtifactWorkspace fileId={artifact.gdrive_file_id} initialContent={artifact.content} />
    </>
  );
}
