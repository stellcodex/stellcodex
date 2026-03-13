import type { FileSummary } from "@/lib/contracts/files";
import { FileActions } from "@/components/files/FileActions";
import { FileStatusBadge } from "@/components/status/FileStatusBadge";

export interface FileHeaderProps {
  file: FileSummary;
}

export function FileHeader({ file }: FileHeaderProps) {
  return (
    <div className="sc-page-head">
      <div className="sc-stack">
        <div className="sc-inline">
          <h1 className="sc-page-title">{file.fileName}</h1>
          <FileStatusBadge status={file.status} />
        </div>
        <span className="sc-muted">{file.fileId}</span>
      </div>
      <FileActions file={file} />
    </div>
  );
}
