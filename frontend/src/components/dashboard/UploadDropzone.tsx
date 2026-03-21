"use client";

import * as React from "react";

import { Button } from "@/components/primitives/Button";
import { Panel } from "@/components/primitives/Panel";
import type { UploadQueueItem } from "@/lib/stores/uploadStore";

export interface UploadDropzoneProps {
  busy?: boolean;
  uploads: UploadQueueItem[];
  onUpload: (file: File) => Promise<void>;
}

export function UploadDropzone({ busy, onUpload, uploads }: UploadDropzoneProps) {
  const inputRef = React.useRef<HTMLInputElement | null>(null);

  async function handleFiles(list: FileList | null) {
    if (!list?.[0]) return;
    await onUpload(list[0]);
  }

  return (
    <Panel
      description="Upload a real manufacturing file and let the worker queue drive status, viewer readiness, and decision flow."
      title="Upload intake"
    >
      <div
        className="rounded-[var(--radius-lg)] border border-dashed border-[var(--border-strong)] bg-[var(--background-subtle)] px-6 py-10 text-center"
        onClick={() => inputRef.current?.click()}
        onDragOver={(event) => event.preventDefault()}
        onDrop={(event) => {
          event.preventDefault();
          void handleFiles(event.dataTransfer.files);
        }}
        onKeyDown={(event) => {
          if (event.key === "Enter" || event.key === " ") {
            event.preventDefault();
            inputRef.current?.click();
          }
        }}
        role="button"
        tabIndex={0}
      >
        <div className="text-lg font-semibold text-[var(--foreground-strong)]">
          {busy ? "Uploading file..." : "Drop a CAD file here or browse"}
        </div>
        <p className="mx-auto mt-2 max-w-xl text-sm text-[var(--foreground-muted)]">
          STEP, STL, DXF, PDF, image, and supported archive flows go through the real backend upload contract. No local-only mode is used.
        </p>
        <Button className="mt-5" variant="primary">
          Select file
        </Button>
        <input
          className="hidden"
          onChange={(event) => {
            void handleFiles(event.target.files);
            event.currentTarget.value = "";
          }}
          ref={inputRef}
          type="file"
        />
      </div>

      {uploads.length > 0 ? (
        <div className="mt-4 space-y-3">
          {uploads.map((upload) => (
            <div key={upload.localId} className="rounded-[var(--radius-md)] border border-[var(--border-muted)] px-4 py-3">
              <div className="flex items-center justify-between gap-4">
                <div>
                  <div className="text-sm font-medium">{upload.fileName}</div>
                  <div className="text-xs text-[var(--foreground-muted)]">
                    {upload.status === "success" && upload.fileId ? `file_id: ${upload.fileId}` : upload.error || upload.status}
                  </div>
                </div>
                <div className="text-sm font-medium">{upload.progress}%</div>
              </div>
              <div className="mt-2 h-2 rounded-full bg-[var(--background-muted)]">
                <div className="h-full rounded-full bg-[var(--accent-default)]" style={{ width: `${upload.progress}%` }} />
              </div>
            </div>
          ))}
        </div>
      ) : null}
    </Panel>
  );
}
