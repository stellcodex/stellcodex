"use client";

import { useCallback, useRef, useState } from "react";
import { Card } from "@/components/ui/Card";
import { PrimaryButton } from "@/components/ui/PrimaryButton";
import { tokens } from "@/lib/tokens";
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

function hasAllowedExt(name: string) {
  const lower = name.toLowerCase();
  return allowedExt.some((ext) => lower.endsWith(ext));
}

export function UploadDrop({ onUploaded }: { onUploaded?: (fileId: string) => void }) {
  const inputRef = useRef<HTMLInputElement | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [status, setStatus] = useState<string | null>(null);

  const handleFile = useCallback(
    async (file: File) => {
      setError(null);
      setStatus(null);

      if (!hasAllowedExt(file.name)) {
        setError(
          "Desteklenmeyen dosya türü. STEP/IGES/BREP/STL/OBJ/PLY/OFF/3MF/AMF/DAE/DXF/PDF/PNG/JPG kabul edilir. DWG ve Parasolid desteklenmez."
        );
        return;
      }
      if (file.size > 100 * 1024 * 1024) {
        setError("Dosya boyutu 100MB limitini aşıyor.");
        return;
      }

      setBusy(true);
      setStatus("Yükleme başlatılıyor...");
      try {
        setStatus("Dosya yükleniyor...");
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
        setStatus("Yükleme tamamlandı. Dosya projeye eklendi.");
        onUploaded?.(registered.fileId);
      } catch (error: unknown) {
        setError(error instanceof Error ? error.message : "Yükleme başarısız.");
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

      <div style={tokens.typography.h2} className="text-[#111827]">Dosya yükle</div>
      <div style={tokens.typography.body} className="mt-2 text-[#6b7280]">
        STEP / IGES / BREP / STL / OBJ / PLY / OFF / 3MF / AMF / DAE / DXF / PDF / PNG / JPG
      </div>

      <div className="mt-4 flex flex-wrap items-center justify-center gap-2">
        <PrimaryButton
          onClick={() => inputRef.current?.click()}
          disabled={busy}
        >
          Dosya seç
        </PrimaryButton>
        <span className="text-xs text-[#6b7280]">Maks: 100MB</span>
      </div>

      {status ? <div className="mt-4 text-sm text-[#6b7280]">{status}</div> : null}
      {error ? <div className="mt-3 text-sm text-red-600">{error}</div> : null}
      </div>
    </Card>
  );
}
