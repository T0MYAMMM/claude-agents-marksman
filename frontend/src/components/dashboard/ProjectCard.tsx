import Link from "next/link";
import { FolderGit2 } from "lucide-react";

import type { Project } from "@/types";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";

export function ProjectCard({ project }: { project: Project }) {
  return (
    <Link href={`/projects/${project.id}`} className="group block">
      <Card className="card-lift gap-3 py-5 transition-all duration-300 ease-[cubic-bezier(0.22,1,0.36,1)] group-hover:-translate-y-1 group-hover:border-brand/40 group-hover:shadow-[var(--shadow-lift)]">
        <CardHeader>
          <CardTitle className="font-display text-lg">{project.name}</CardTitle>
          {project.description && (
            <CardDescription className="line-clamp-2">
              {project.description}
            </CardDescription>
          )}
        </CardHeader>
        <CardContent className="flex items-center justify-between text-xs text-muted-foreground">
          <span className="inline-flex items-center gap-1.5">
            <FolderGit2 className="size-3.5" />
            <span className="font-mono">
              {project.gdrive_folder_id.slice(0, 12)}…
            </span>
          </span>
          <span>Updated {new Date(project.updated_at).toLocaleDateString()}</span>
        </CardContent>
      </Card>
    </Link>
  );
}
