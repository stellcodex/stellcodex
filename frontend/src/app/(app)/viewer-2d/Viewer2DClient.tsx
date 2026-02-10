"use client";

import { useEffect, useRef, useState } from "react";
import { useSearchParams } from "next/navigation";
import { PageShell } from "@/components/layout/PageShell";
import { DxfViewer } from "@/components/viewer/DxfViewer";
import { fetchAuthedBlobUrl, getFile } from "@/services/api";

export default function Viewer2DClient() {
  const params = useSearchParams();
  const fileId = params.get("fileId");
  const [url, setUrl] = useState<string | null>(null);
  const [contentType, setContentType] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isDxf, setIsDxf] = useState(false);
  const sourceUrlRef = useRef<string | null>(null);
  const objectUrlRef = useRef<string | null>(null);

  useEffect(() => {
    if (!fileId) {
      setError("Dosya seçilmedi.");
      return;
    }
    setUrl(null);
    setError(null);
    setIsDxf(false);
    sourceUrlRef.current = null;
    if (objectUrlRef.current) {
      URL.revokeObjectURL(objectUrlRef.current);
      objectUrlRef.current = null;
    }
    let cancelled = false;
    const load = async () => {
      try {
        const f = await getFile(fileId);
        if (cancelled) return;
        if (f.status === "failed") {
          setError(f.error || "Dönüştürme başarısız.");
          return;
        }
        if (f.status !== "ready") {
          setError("Model işleniyor. Lütfen bekleyin.");
          return;
        }
        const dxf = f.original_filename.toLowerCase().endsWith(".dxf");
        setIsDxf(dxf);
        if (dxf) {
          setError(null);
          setUrl(null);
          setContentType(null);
          return;
        }
        if (!f.original_url) {
          setError("2D içerik hazır değil.");
          return;
        }
        if (sourceUrlRef.current === f.original_url && objectUrlRef.current) {
          return;
        }
        const blobUrl = await fetchAuthedBlobUrl(f.original_url);
        if (cancelled) {
          URL.revokeObjectURL(blobUrl);
          return;
        }
        if (objectUrlRef.current) {
          URL.revokeObjectURL(objectUrlRef.current);
        }
        objectUrlRef.current = blobUrl;
        sourceUrlRef.current = f.original_url;
        setError(null);
        setUrl(blobUrl);
        setContentType(f.content_type);
      } catch (e: any) {
        if (!cancelled) setError(e?.message || "Dosya yüklenemedi.");
      }
    };
    void load();
    const id = setInterval(load, 5000);
    return () => {
      cancelled = true;
      clearInterval(id);
      if (objectUrlRef.current) {
        URL.revokeObjectURL(objectUrlRef.current);
        objectUrlRef.current = null;
      }
    };
  }, [fileId]);

  return (
    <PageShell title="2D Viewer" subtitle="PDF ve görsel dosyaları için hızlı görüntüleme.">
      <div className="h-[75vh] rounded-3xl border border-slate-200 bg-white p-4">
        {!fileId ? (
          <div className="text-sm text-slate-600">
            Dosya seçilmedi. Önce <a className="underline" href="/files">Yüklemeler</a> sayfasından bir dosya seç.
          </div>
        ) : error ? (
          <div className="text-sm text-red-600">{error}</div>
        ) : isDxf ? (
          <DxfViewer fileId={fileId} />
        ) : url ? (
          contentType === "application/pdf" ? (
            <iframe src={url} className="h-full w-full rounded-2xl" />
          ) : (
            <img src={url} alt="2D preview" className="h-full w-full object-contain" />
          )
        ) : (
          <div className="text-sm text-slate-500">Yükleniyor...</div>
        )}
      </div>
    </PageShell>
  );
}
