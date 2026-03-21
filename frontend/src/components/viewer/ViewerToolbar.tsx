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
    <div className="flex flex-col gap-4 border-b border-[#eeeeee] bg-white px-4 py-4 lg:flex-row lg:items-center lg:justify-between">
      <div className="space-y-1">
        <div className="text-[18px] font-semibold text-[var(--foreground-strong)]">{file.originalName}</div>
        <div className="flex items-center gap-3">
          <FileStatusBadge status={file.status} />
          <span className="text-sm text-[var(--foreground-muted)]">{file.fileId}</span>
        </div>
      </div>
      <div className="flex flex-wrap items-center gap-2">
        <Button onClick={onFitModel} size="sm" variant="secondary">Fit model</Button>
        <Button onClick={onFitSelection} size="sm" variant="secondary">Fit selection</Button>
        <Button onClick={onResetView} size="sm" variant="secondary">Reset</Button>
        <Button onClick={onOpenShare} size="sm" variant="secondary">Share</Button>
        <Link href={`/files/${encodeURIComponent(file.fileId)}/versions`}>
          <Button size="sm" variant="secondary">Versions</Button>
        </Link>
        <Button onClick={onToggleFullscreen} size="sm" variant="secondary">Fullscreen</Button>
      </div>
    </div>
  );
}
