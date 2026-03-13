import type { FileSummary } from "@/lib/contracts/files";
import { Panel } from "@/components/primitives/Panel";
import { formatFileSize } from "@/lib/utils/file";

export interface FileSummaryCardProps {
  file: FileSummary;
}

export function FileSummaryCard({ file }: FileSummaryCardProps) {
  return (
    <Panel title="File summary">
      <dl className="sc-kv">
        <dt>File ID</dt>
        <dd>{file.fileId}</dd>
        <dt>Size</dt>
        <dd>{formatFileSize(file.sizeBytes)}</dd>
        <dt>Content type</dt>
        <dd>{file.mimeType || "Unknown"}</dd>
        <dt>Viewer</dt>
        <dd>{file.viewerReady ? "Ready" : "Not ready"}</dd>
      </dl>
    </Panel>
  );
}
