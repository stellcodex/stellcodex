"use client";

import Link from "next/link";

import { Button } from "@/components/primitives/Button";
import type { FileRecord } from "@/lib/contracts/ui";

import { FileStatusBadge } from "../files/FileStatusBadge";

export interface ViewerToolbarProps {
  file: FileRecord;
  onFitModel: () => void;
  onFitSelection: () => void;
  onResetView: () => void;
  onOpenShare: () => void;
  onToggleFullscreen: () => void;
}

export function ViewerToolbar({
  file,
  onFitModel,
  onFitSelection,
  onOpenShare,
  onResetView,
  onToggleFullscreen,
}: ViewerToolbarProps) {
  return (
    <div className="flex flex-col gap-4 border-b border-[var(--border-muted)] bg-[var(--background-surface)] px-5 py-4 lg:flex-row lg:items-center lg:justify-between">
      <div className="space-y-1">
        <div className="text-lg font-semibold text-[var(--foreground-strong)]">{file.originalName}</div>
        <div className="flex items-center gap-3">
          <FileStatusBadge status={file.status} />
          <span className="text-xs text-[var(--foreground-muted)]">{file.fileId}</span>
        </div>
      </div>
      <div className="flex flex-wrap items-center gap-2">
        <Button onClick={onFitModel} size="sm">Fit model</Button>
        <Button onClick={onFitSelection} size="sm">Fit selection</Button>
        <Button onClick={onResetView} size="sm">Reset</Button>
        <Button onClick={onOpenShare} size="sm">Share</Button>
        <Link href={`/files/${encodeURIComponent(file.fileId)}/versions`}>
          <Button size="sm">Versions</Button>
        </Link>
        <Button onClick={onToggleFullscreen} size="sm">Fullscreen</Button>
      </div>
    </div>
  );
}
