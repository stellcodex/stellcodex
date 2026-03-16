import Link from "next/link";

import { Card } from "@/components/primitives/Card";
import type { FileRecord } from "@/lib/contracts/ui";
import { formatBytes, formatDateTime } from "@/lib/utils";

import { FileStatusBadge } from "./FileStatusBadge";

export interface FileMetaCardProps {
  file: FileRecord;
  projectName: string | null;
}

export function FileMetaCard({ file, projectName }: FileMetaCardProps) {
  return (
    <Card description="File identity and lifecycle are anchored on file_id only." title="File metadata">
      <dl className="grid gap-4 text-sm md:grid-cols-2">
        <div>
          <dt className="text-[var(--foreground-soft)]">file_id</dt>
          <dd className="mt-1 font-medium">{file.fileId}</dd>
        </div>
        <div>
          <dt className="text-[var(--foreground-soft)]">Status</dt>
          <dd className="mt-1">
            <FileStatusBadge status={file.status} />
          </dd>
        </div>
        <div>
          <dt className="text-[var(--foreground-soft)]">Original name</dt>
          <dd className="mt-1 font-medium">{file.originalName}</dd>
        </div>
        <div>
          <dt className="text-[var(--foreground-soft)]">Type</dt>
          <dd className="mt-1 font-medium">{file.kind}</dd>
        </div>
        <div>
          <dt className="text-[var(--foreground-soft)]">Mode</dt>
          <dd className="mt-1 font-medium">{file.mode || "Unknown"}</dd>
        </div>
        <div>
          <dt className="text-[var(--foreground-soft)]">Size</dt>
          <dd className="mt-1 font-medium">{formatBytes(file.sizeBytes)}</dd>
        </div>
        <div>
          <dt className="text-[var(--foreground-soft)]">Created</dt>
          <dd className="mt-1 font-medium">{formatDateTime(file.createdAt)}</dd>
        </div>
        <div>
          <dt className="text-[var(--foreground-soft)]">Project</dt>
          <dd className="mt-1 font-medium">
            {projectName ? <Link href="/projects">{projectName}</Link> : "Not linked"}
          </dd>
        </div>
      </dl>
    </Card>
  );
}
