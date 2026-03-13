"use client";

import { useRef } from "react";
import { Button } from "@/components/primitives/Button";
import { Panel } from "@/components/primitives/Panel";

type UploadDropzoneProps = {
  helperText?: string;
  error?: string | null;
  isUploading?: boolean;
  onFilesSelected: (files: File[]) => void;
};

export function UploadDropzone({ helperText, error, isUploading, onFilesSelected }: UploadDropzoneProps) {
  const inputRef = useRef<HTMLInputElement | null>(null);

  return (
    <Panel title="Upload" subtitle={helperText || "Drop a file or choose one to start processing."}>
      <div
        className="sc-empty"
        onDragOver={(event) => event.preventDefault()}
        onDrop={(event) => {
          event.preventDefault();
          const files = Array.from(event.dataTransfer.files || []);
          if (files.length > 0) onFilesSelected(files);
        }}
      >
        <strong>Drag and drop files here</strong>
        <span className="sc-muted">Accepted engineering formats come from the backend registry. Upload uses file_id only.</span>
        {error ? <span>{error}</span> : null}
        <div className="sc-inline">
          <Button variant="primary" onClick={() => inputRef.current?.click()} disabled={isUploading}>
            Select file
          </Button>
          <input
            ref={inputRef}
            className="hidden-input"
            type="file"
            onChange={(event) => {
              const files = Array.from(event.target.files || []);
              if (files.length > 0) onFilesSelected(files);
              event.currentTarget.value = "";
            }}
          />
        </div>
      </div>
    </Panel>
  );
}
