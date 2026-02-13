"use client";

import { useEffect, useRef, useState } from "react";
import { useSearchParams } from "next/navigation";
import { PageShell } from "@/components/layout/PageShell";
import { fetchAuthedBlobUrl, getFile } from "@/services/api";
import { RenderMode, ThreeViewer } from "@/components/viewer/ThreeViewer";

export default function Viewer3DClient() {
  const params = useSearchParams();
  const fileId = params.get("fileId");
  const [url, setUrl] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [renderMode, setRenderMode] = useState<RenderMode>("shadedEdges");
  const [clip, setClip] = useState(false);
  const [clipOffset, setClipOffset] = useState(0);
  const [nodes, setNodes] = useState<{ name: string; type: string }[]>([]);
  const sourceUrlRef = useRef<string | null>(null);
  const objectUrlRef = useRef<string | null>(null);

  useEffect(() => {
    if (!fileId) {
      setError("Dosya seçilmedi.");
      return;
    }
    setUrl(null);
    setError(null);
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
        if (!f.gltf_url) {
          setError("3D içerik hazır değil.");
          return;
        }
        if (sourceUrlRef.current === f.gltf_url && objectUrlRef.current) {
          return;
        }
        const blobUrl = await fetchAuthedBlobUrl(f.gltf_url);
        if (cancelled) {
          URL.revokeObjectURL(blobUrl);
          return;
        }
        if (objectUrlRef.current) {
          URL.revokeObjectURL(objectUrlRef.current);
        }
        objectUrlRef.current = blobUrl;
        sourceUrlRef.current = f.gltf_url;
        setError(null);
        setUrl(blobUrl);
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
    <PageShell title="3D Görüntüleyici" subtitle="Yörünge / Kaydırma / Yakınlaşma, kesit ve tel kafes.">
      <div className="grid gap-4 lg:grid-cols-[1fr_280px]">
        <div className="h-[70vh] rounded-3xl border border-slate-200 bg-white">
          {!fileId ? (
            <div className="p-4 text-sm text-slate-600">
              Dosya seçilmedi. Önce{" "}
              <a className="underline" href="/files">
                Yüklemeler
              </a>{" "}
              sayfasından bir dosya seç.
            </div>
          ) : error ? (
            <div className="p-4 text-sm text-red-600">{error}</div>
          ) : url ? (
            <ThreeViewer
              url={url}
              renderMode={renderMode}
              clip={clip}
              clipOffset={clipOffset}
              onNodes={(list) => setNodes(list.map((n) => ({ name: n.name, type: n.type })))}
            />
          ) : (
            <div className="p-4 text-sm text-slate-500">Model yükleniyor...</div>
          )}
        </div>

        <div className="rounded-3xl border border-slate-200 bg-white p-4">
          <div className="text-sm font-semibold text-slate-900">Görünüm</div>
          <div className="mt-3 grid gap-2 text-sm">
            <label className="text-xs text-slate-600">Mod</label>
            <select
              value={renderMode}
              onChange={(e) => setRenderMode(e.target.value as RenderMode)}
              className="rounded-lg border border-slate-300 bg-white px-2 py-1 text-sm"
            >
              <option value="shaded">Shaded</option>
              <option value="shadedEdges">Shaded + Edges</option>
              <option value="xray">X-Ray</option>
              <option value="wireframe">Wireframe</option>
              <option value="pbr">PBR</option>
            </select>
            <label className="flex items-center justify-between">
              Kesit Düzlemi
              <input type="checkbox" checked={clip} onChange={(e) => setClip(e.target.checked)} />
            </label>
            {clip ? (
              <input
                type="range"
                min={-2}
                max={2}
                step={0.01}
                value={clipOffset}
                onChange={(e) => setClipOffset(Number(e.target.value))}
              />
            ) : null}
            <div className="text-[11px] text-slate-500">
              Offline render ayrı job hattıdır; viewer modu değildir.
            </div>
          </div>

          <div className="mt-6 text-sm font-semibold text-slate-900">Model Ağacı</div>
          <div className="mt-2 max-h-64 overflow-auto text-xs text-slate-600">
            {nodes.length === 0 ? (
              <div className="text-slate-400">Düğüm bulunamadı.</div>
            ) : (
              nodes.map((n, i) => (
                <div key={`${n.name}-${i}`} className="py-1">
                  {n.name} <span className="text-slate-400">({n.type})</span>
                </div>
              ))
            )}
          </div>
        </div>
      </div>
    </PageShell>
  );
}
