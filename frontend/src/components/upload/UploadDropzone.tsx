"use client";

import { useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { Button } from "@/components/common/Button";
import { ProcessingScreen } from "@/components/upload/ProcessingScreen";
import { getDefaultProject, getJob, uploadFile } from "@/lib/api";

const ALLOWED_EXT = [
  "step",
  "stp",
  "iges",
  "igs",
  "stl",
  "obj",
  "sldprt",
  "dxf",
  "pdf",
  "jpg",
  "jpeg",
  "png",
  "webp",
  "docx",
  "xlsx",
  "pptx",
  "zip",
];
const MAX_BYTES = 200 * 1024 * 1024;

function extOf(name: string) {
  return (name.split(".").pop() || "").toLowerCase();
}

export function UploadDropzone() {
  const inputRef = useRef<HTMLInputElement | null>(null);
  const router = useRouter();
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [job, setJob] = useState<{ stage: "uploaded" | "security" | "preview" | "ready"; progress: number } | null>(null);

  async function poll(jobId: string, fileId: string) {
    for (let i = 0; i < 80; i++) {
      const next = await getJob(jobId);
      setJob({ stage: next.stage, progress: next.progress });
      if (next.stage === "ready" && (next.status === "SUCCEEDED" || next.status === "NEEDS_APPROVAL")) {
        router.push(`/view/file/${fileId}`);
        return;
      }
      await new Promise((r) => setTimeout(r, 700));
    }
    setError("İşleme beklenenden uzun sürdü. Lütfen tekrar deneyin.");
    setBusy(false);
  }

  async function handleFile(file: File) {
    setError(null);
    if (!ALLOWED_EXT.includes(extOf(file.name))) {
      setError("Desteklenmeyen dosya uzantısı.");
      return;
    }
    if (file.size > MAX_BYTES) {
      setError("Dosya boyutu limiti 200MB. Daha küçük dosya yükleyin.");
      return;
    }
    setBusy(true);
    setJob({ stage: "uploaded", progress: 8 });
    try {
      const project = await getDefaultProject();
      const result = await uploadFile(file, project.projectId);
      await poll(result.jobId, result.fileId);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Yükleme başarısız.");
      setBusy(false);
    }
  }

  return (
    <div className="w-full max-w-2xl">
      {job && busy ? (
        <ProcessingScreen stage={job.stage} progress={job.progress} />
      ) : (
        <div className="rounded-3xl border border-slate-200 bg-white p-8 shadow-sm">
          <div className="text-center">
            <h1 className="text-3xl font-semibold tracking-tight text-slate-900 sm:text-4xl">
              STELLCODEX
            </h1>
            <p className="mt-3 text-sm text-slate-600">
              Dosyayı yükleyin. Sistem uygun klasöre yerleştirir ve StellView için hazırlar.
            </p>
          </div>
          <div className="mt-7 flex flex-col items-center gap-3">
            <Button size="lg" variant="primary" onClick={() => inputRef.current?.click()}>
              Dosya Yükle
            </Button>
            <input
              ref={inputRef}
              type="file"
              className="hidden"
              onChange={(e) => {
                const file = e.target.files?.[0];
                e.target.value = "";
                if (file) void handleFile(file);
              }}
            />
            <p className="text-xs text-slate-500">
              Desteklenenler: STEP, STL, DXF, PDF, JPG/PNG/WEBP, DOCX/XLSX/PPTX, ZIP
            </p>
          </div>
        </div>
      )}
      {error ? <p className="mt-3 text-sm text-red-600">{error}</p> : null}
    </div>
  );
}

