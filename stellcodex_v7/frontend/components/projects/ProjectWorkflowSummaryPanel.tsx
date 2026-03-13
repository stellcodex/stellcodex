import type { ProjectDetail } from "@/lib/contracts/projects";
import { Panel } from "@/components/primitives/Panel";
import { Badge } from "@/components/primitives/Badge";

export interface ProjectWorkflowSummaryPanelProps {
  project: ProjectDetail;
}

export function ProjectWorkflowSummaryPanel({ project }: ProjectWorkflowSummaryPanelProps) {
  return (
    <Panel title="Workflow summary">
      <div className="sc-inline">
        <Badge variant="success">Ready {project.readyCount || 0}</Badge>
        <Badge variant="warning">Processing {project.processingCount || 0}</Badge>
        <Badge variant="danger">Failed {project.failedCount || 0}</Badge>
      </div>
    </Panel>
  );
}
