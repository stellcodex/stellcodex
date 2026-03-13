import type { FileSummary } from "@/lib/contracts/files";
import { Panel } from "@/components/primitives/Panel";

export interface ProjectActivityPanelProps {
  files: FileSummary[];
}

export function ProjectActivityPanel({ files }: ProjectActivityPanelProps) {
  return (
    <Panel title="Recent activity">
      <div className="sc-stack">
        {files.slice(0, 5).map((file) => (
          <div key={file.fileId} className="sc-inline" style={{ justifyContent: "space-between" }}>
            <span>{file.fileName}</span>
            <span className="sc-muted">{file.updatedAt || file.createdAt || "No timestamp"}</span>
          </div>
        ))}
        {files.length === 0 ? <span className="sc-muted">No activity yet</span> : null}
      </div>
    </Panel>
  );
}
