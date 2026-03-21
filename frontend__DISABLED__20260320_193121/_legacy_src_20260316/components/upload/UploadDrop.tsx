"use client";

import { useCallback, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { Card } from "@/components/ui/Card";
import { PrimaryButton } from "@/components/ui/PrimaryButton";
import { tokens } from "@/lib/tokens";
import { resolveFileAppPath } from "@/lib/workspace-routing";
import { uploadDirect } from "@/services/api";
import { ALLOWED_FORMATS } from "@/lib/formats.generated";
import {
  DEFAULT_PROJECT_ID,
  DEFAULT_PROJECT_NAME,
  detectWorkspaceMode,
  registerUploadedFile,
  type WorkspaceMode,
} from "@/lib/workspace-store";

const allowedExt = ALLOWED_FORMATS.map((ext) => `.${ext}`);
const supportedFormatsCopy = ALLOWED_FORMATS.map((ext) => ext.toUpperCase()).join(" / ");
const MAX_UPLOAD_MB = 200;
const MAX_UPLOAD_BYTES = MAX_UPLOAD_MB * 1024 * 1024;

function hasAllowedExt(name: string) {
  const lower = name.toLowerCase();
  return allowedExt.some((ext) => lower.endsWith(ext));
}

export function UploadDrop({ onUploaded }: { onUploaded?: (fileId: string) => void }) {
  const inputRef = useRef<HTMLInputElement | null>(null);
  const router = useRouter();
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [status, setStatus] = useState<string | null>(null);

  const handleFile = useCallback(
    async (file: File) => {
      setError(null);
      setStatus(null);

      if (!hasAllowedExt(file.name)) {
        setError("Unsupported file type. Accepted extensions follow the active backend registry listed below.");
        return;
      }
      if (file.size > MAX_UPLOAD_BYTES) {
        setError(`The file exceeds the ${MAX_UPLOAD_MB}MB limit.`);
        return;
      }

      setBusy(true);
      setStatus("Preparing upload...");
      try {
        setStatus("Uploading file...");
        const res = await uploadDirect(file);
        const mode: WorkspaceMode = detectWorkspaceMode(file.name, file.type || null);
        const registered = registerUploadedFile({
          fileId: res.file_id,
          originalFilename: file.name,
          sizeBytes: file.size,
          contentType: file.type || null,
          mode,
          projectId: DEFAULT_PROJECT_ID,
          projectName: DEFAULT_PROJECT_NAME,
        });
        // Public upload uses the same routing rule as the suite home: file type decides the app.
        const destination = resolveFileAppPath(null, { original_filename: file.name, content_type: file.type || null }, registered.fileId);
        setStatus("Opening the responsible application...");
        onUploaded?.(registered.fileId);
        const target = destination.href;
        router.push(target);
        window.setTimeout(() => {
          if (window.location.pathname !== target) {
            window.location.assign(target);
          }
        }, 1500);
      } catch (error: unknown) {
        setStatus(null);
        setError(error instanceof Error ? error.message : "Upload failed.");
      } finally {
        setBusy(false);
      }
    },
    [onUploaded]
  );

  return (
    <Card className="p-5 text-center">
      <div
        className="rounded-2xl border border-dashed border-[#d1d5db] bg-white p-5"
        onDragOver={(e) => {
          e.preventDefault();
          e.stopPropagation();
        }}
        onDrop={(e) => {
          e.preventDefault();
          const file = e.dataTransfer.files?.[0];
          if (file) void handleFile(file);
        }}
      >
      <input
        ref={inputRef}
        type="file"
        accept={allowedExt.join(",")}
        className="hidden"
        onChange={(e) => {
          const file = e.target.files?.[0];
          if (file) void handleFile(file);
        }}
      />

      <div style={tokens.typography.h2} className="text-[#111827]">Upload file</div>
      <div style={tokens.typography.body} className="mt-2 text-[#6b7280]">
        The suite routes the file to 3D, 2D, or Documents automatically.
      </div>
      <div className="mt-2 text-xs text-[#6b7280]">
        Supported formats: {supportedFormatsCopy}
      </div>

      <div className="mt-4 flex flex-wrap items-center justify-center gap-2">
        <PrimaryButton
          onClick={() => inputRef.current?.click()}
          disabled={busy}
        >
          Select file
        </PrimaryButton>
        <span className="text-xs text-[#6b7280]">Max: {MAX_UPLOAD_MB}MB</span>
      </div>

      {status ? <div className="mt-4 text-sm text-[#6b7280]">{status}</div> : null}
      {error ? <div className="mt-3 text-sm text-red-600">{error}</div> : null}
      </div>
    </Card>
  );
}
