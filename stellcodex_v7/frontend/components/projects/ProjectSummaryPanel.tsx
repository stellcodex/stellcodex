import type { ProjectDetail } from "@/lib/contracts/projects";
import { Panel } from "@/components/primitives/Panel";

export interface ProjectSummaryPanelProps {
  project: ProjectDetail;
}

export function ProjectSummaryPanel({ project }: ProjectSummaryPanelProps) {
  return (
    <Panel title="Project summary">
      <dl className="sc-kv">
        <dt>Total files</dt>
        <dd>{project.filesCount || 0}</dd>
        <dt>Ready</dt>
        <dd>{project.readyCount || 0}</dd>
        <dt>Processing</dt>
        <dd>{project.processingCount || 0}</dd>
        <dt>Failed</dt>
        <dd>{project.failedCount || 0}</dd>
      </dl>
    </Panel>
  );
}
