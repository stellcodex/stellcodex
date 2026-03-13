"use client";

import Link from "next/link";
import { FitControls } from "@/components/viewer/FitControls";
import { Button } from "@/components/primitives/Button";
import type { FileSummary } from "@/lib/contracts/files";

export interface ViewerToolbarProps {
  file: FileSummary;
  onFit: () => void;
  onReset: () => void;
  shareHref?: string | null;
}

export function ViewerToolbar({ file, onFit, onReset, shareHref }: ViewerToolbarProps) {
  return (
    <div className="sc-page-head">
      <div className="sc-stack">
        <strong>{file.fileName}</strong>
        <span className="sc-muted">{file.fileId}</span>
      </div>
      <div className="sc-inline">
        <FitControls onFit={onFit} onReset={onReset} />
        {shareHref ? (
          <Link href={shareHref} className="sc-button" data-variant="ghost">
            Share
          </Link>
        ) : (
          <Button variant="ghost" disabled>
            Share unavailable
          </Button>
        )}
      </div>
    </div>
  );
}
