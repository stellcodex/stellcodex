import { ProjectActions } from "@/components/projects/ProjectActions";
import type { ProjectDetail } from "@/lib/contracts/projects";

export interface ProjectHeaderProps {
  project: ProjectDetail;
}

export function ProjectHeader({ project }: ProjectHeaderProps) {
  return (
    <div className="sc-page-head">
      <div className="sc-stack">
        <h1 className="sc-page-title">{project.name}</h1>
        <span className="sc-muted">{project.description || "Engineering project workspace"}</span>
      </div>
      <ProjectActions project={project} />
    </div>
  );
}
