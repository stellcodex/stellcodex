import { ProjectDetailScreen } from "@/components/projects/ProjectDetailScreen";

export interface ProjectWorkspaceProps {
  projectId: string;
}

export function ProjectWorkspace({ projectId }: ProjectWorkspaceProps) {
  return <ProjectDetailScreen projectId={projectId} />;
}
