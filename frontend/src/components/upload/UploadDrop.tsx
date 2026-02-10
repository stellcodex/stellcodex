"use client";

import { useCallback, useRef, useState } from "react";
import { Button } from "@/components/ui/Button";
import { uploadDirect } from "@/services/api";

const allowedExt = [
  ".stl",
  ".step",
  ".stp",
  ".iges",
  ".igs",
  ".brep",
  ".brp",
  ".fcstd",
  ".ifc",
  ".obj",
  ".ply",
  ".off",
  ".3mf",
  ".amf",
  ".dae",
  ".glb",
  ".gltf",
  ".dxf",
  ".pdf",
  ".png",
  ".jpg",
  ".jpeg",
];

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
          "Desteklenmeyen dosya türü. STEP/IGES/BREP/FCStd/IFC/STL/OBJ/PLY/OFF/3MF/AMF/DAE/GLB/GLTF/DXF/PDF/PNG/JPG kabul edilir. DWG ve SVG desteklenmez."
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
        setStatus("Yükleme tamamlandı.");
        onUploaded?.(res.file_id);
      } catch (e: any) {
        setError(e?.message || "Yükleme başarısız.");
      } finally {
        setBusy(false);
      }
    },
    [onUploaded]
  );

  return (
    <div
      className="rounded-3xl border border-dashed border-slate-300 bg-white p-6 text-center"
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
        accept=".stl,.step,.stp,.iges,.igs,.brep,.brp,.fcstd,.ifc,.obj,.ply,.off,.3mf,.amf,.dae,.glb,.gltf,.dxf,.pdf,.png,.jpg,.jpeg"
        className="hidden"
        onChange={(e) => {
          const file = e.target.files?.[0];
          if (file) void handleFile(file);
        }}
      />

      <div className="text-sm font-semibold text-slate-900">Dosya Yükle</div>
      <div className="mt-2 text-sm text-slate-600">
        STEP / IGES / BREP / FCStd / IFC / STL / OBJ / PLY / OFF / 3MF / AMF / DAE / GLB / GLTF / DXF / PDF / PNG / JPG
      </div>

      <div className="mt-4 flex flex-wrap items-center justify-center gap-2">
        <Button
          onClick={() => inputRef.current?.click()}
          disabled={busy}
        >
          Dosya Seç
        </Button>
        <span className="text-xs text-slate-500">Maks: 100MB</span>
      </div>

      {status ? <div className="mt-4 text-sm text-slate-700">{status}</div> : null}
      {error ? <div className="mt-3 text-sm text-red-600">{error}</div> : null}
    </div>
  );
}
