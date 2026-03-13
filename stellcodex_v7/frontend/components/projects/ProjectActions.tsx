import Link from "next/link";
import type { ProjectDetail } from "@/lib/contracts/projects";
import { Button } from "@/components/primitives/Button";

export interface ProjectActionsProps {
  project: Pick<ProjectDetail, "projectId">;
}

export function ProjectActions({ project }: ProjectActionsProps) {
  return (
    <div className="sc-inline">
      <Link href="/projects" className="sc-button" data-variant="ghost">
        All projects
      </Link>
      <Button variant="ghost" disabled>
        New file
      </Button>
      <Link href={`/projects/${project.projectId}`} className="sc-button" data-variant="ghost">
        Refresh
      </Link>
    </div>
  );
}
