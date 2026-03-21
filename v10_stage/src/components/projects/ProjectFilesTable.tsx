import Link from "next/link";

import { EmptyState } from "@/components/primitives/EmptyState";
import { Table } from "@/components/primitives/Table";
import type { ProjectFileRecord } from "@/lib/contracts/ui";
import { formatDateTime } from "@/lib/utils";

import { FileStatusBadge } from "../files/FileStatusBadge";

export interface ProjectFilesTableProps {
  files: ProjectFileRecord[];
  onShare?: (fileId: string) => void;
  onStartWorkflow?: (fileId: string) => void | Promise<void>;
  startingFileId?: string | null;
}

export function ProjectFilesTable({ files, onShare, onStartWorkflow, startingFileId }: ProjectFilesTableProps) {
  if (files.length === 0) {
    return <EmptyState description="Upload a file into this project to start the decision flow." title="No files in project" />;
  }

  return (
    <Table>
      <thead className="bg-[var(--background-subtle)] text-left text-xs uppercase tracking-[0.16em] text-[var(--foreground-soft)]">
        <tr>
          <th className="px-4 py-3">File</th>
          <th className="px-4 py-3">Status</th>
          <th className="px-4 py-3">Created</th>
          <th className="px-4 py-3" />
        </tr>
      </thead>
      <tbody>
        {files.map((file) => (
          <tr key={file.fileId} className="border-t border-[var(--border-muted)]">
            <td className="px-4 py-3">
              <div className="font-medium">{file.originalFilename}</div>
              <div className="text-xs text-[var(--foreground-muted)]">{file.fileId}</div>
            </td>
            <td className="px-4 py-3">
              <FileStatusBadge status={file.status} />
            </td>
            <td className="px-4 py-3">{formatDateTime(file.createdAt)}</td>
            <td className="px-4 py-3 text-right">
              <div className="flex justify-end gap-3">
                <Link className="font-medium" href={`/files/${encodeURIComponent(file.fileId)}`}>
                  File
                </Link>
                <Link className="font-medium" href={`/files/${encodeURIComponent(file.fileId)}/viewer`}>
                  Viewer
                </Link>
                {onStartWorkflow ? (
                  <button
                    className="font-medium disabled:cursor-not-allowed disabled:opacity-50"
                    disabled={startingFileId === file.fileId}
                    onClick={() => void onStartWorkflow(file.fileId)}
                    type="button"
                  >
                    {startingFileId === file.fileId ? "Starting..." : "Start workflow"}
                  </button>
                ) : null}
                {onShare ? (
                  <button className="font-medium" onClick={() => onShare(file.fileId)} type="button">
                    Share
                  </button>
                ) : null}
              </div>
            </td>
          </tr>
        ))}
      </tbody>
    </Table>
  );
}
