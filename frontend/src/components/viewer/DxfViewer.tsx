"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { DxfManifest, getDxfManifest, getDxfRender } from "@/services/api";

export function DxfViewer({ fileId }: { fileId: string }) {
  const [manifest, setManifest] = useState<DxfManifest | null>(null);
  const [activeLayers, setActiveLayers] = useState<Set<string>>(new Set());
  const [svgUrl, setSvgUrl] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [scale, setScale] = useState(1);
  const [offset, setOffset] = useState({ x: 0, y: 0 });
  const dragging = useRef(false);
  const lastPos = useRef({ x: 0, y: 0 });
  const svgRef = useRef<string | null>(null);
  const manifestLoadedRef = useRef(false);
  const viewportRef = useRef<HTMLDivElement | null>(null);

  const layerList = useMemo(() => manifest?.layers ?? [], [manifest]);

  const isPendingError = (value: string) => {
    const msg = value.toLowerCase();
    return msg.includes("not ready") || msg.includes("hazır değil") || msg.includes("hazirlaniyor") || msg.includes("hazırlanıyor");
  };

  useEffect(() => {
    let cancelled = false;
    setManifest(null);
    setError(null);
    manifestLoadedRef.current = false;
    if (svgRef.current) {
      URL.revokeObjectURL(svgRef.current);
      svgRef.current = null;
    }
    setSvgUrl(null);
    setScale(1);
    setOffset({ x: 0, y: 0 });

    const load = async () => {
      try {
        const data = await getDxfManifest(fileId);
        if (cancelled) return;
        setManifest(data);
        if (!manifestLoadedRef.current) {
          const initial = new Set(data.layers.filter((l) => l.is_visible).map((l) => l.name));
          setActiveLayers(initial);
        }
        manifestLoadedRef.current = true;
        setError(null);
      } catch (e: any) {
        if (cancelled) return;
        const message = e?.message || "DXF manifest alınamadı.";
        if (isPendingError(message)) {
          setError(null);
          return;
        }
        setError(message);
      }
    };
    void load();
    const timer = window.setInterval(() => {
      if (!manifestLoadedRef.current) {
        void load();
      }
    }, 3000);

    return () => {
      cancelled = true;
      window.clearInterval(timer);
    };
  }, [fileId]);

  useEffect(() => {
    if (!manifest) return;
    let cancelled = false;
    const render = async () => {
      try {
        const url = await getDxfRender(fileId, Array.from(activeLayers));
        if (cancelled) {
          URL.revokeObjectURL(url);
          return;
        }
        if (svgRef.current) {
          URL.revokeObjectURL(svgRef.current);
        }
        svgRef.current = url;
        setSvgUrl(url);
        setError(null);
      } catch (e: any) {
        if (cancelled) return;
        const message = e?.message || "DXF render başarısız.";
        if (isPendingError(message)) {
          setError(null);
          return;
        }
        setError(message);
      }
    };
    void render();

    return () => {
      cancelled = true;
    };
  }, [fileId, manifest, activeLayers]);

  useEffect(() => {
    return () => {
      if (svgRef.current) {
        URL.revokeObjectURL(svgRef.current);
        svgRef.current = null;
      }
    };
  }, []);

  const applyWheelZoom = useCallback((deltaY: number) => {
    const delta = deltaY < 0 ? 1.1 : 0.9;
    setScale((s) => Math.min(10, Math.max(0.2, s * delta)));
  }, []);

  useEffect(() => {
    const host = viewportRef.current;
    if (!host) return;
    const onWheel = (event: WheelEvent) => {
      event.preventDefault();
      applyWheelZoom(event.deltaY);
    };
    host.addEventListener("wheel", onWheel, { passive: false });
    return () => {
      host.removeEventListener("wheel", onWheel);
    };
  }, [applyWheelZoom]);

  const resetFit = () => {
    setScale(1);
    setOffset({ x: 0, y: 0 });
  };

  const onPointerDown = (e: React.PointerEvent<HTMLDivElement>) => {
    dragging.current = true;
    lastPos.current = { x: e.clientX, y: e.clientY };
    (e.currentTarget as HTMLElement).setPointerCapture(e.pointerId);
  };

  const onPointerMove = (e: React.PointerEvent<HTMLDivElement>) => {
    if (!dragging.current) return;
    const dx = e.clientX - lastPos.current.x;
    const dy = e.clientY - lastPos.current.y;
    lastPos.current = { x: e.clientX, y: e.clientY };
    setOffset((o) => ({ x: o.x + dx, y: o.y + dy }));
  };

  const onPointerUp = (e: React.PointerEvent<HTMLDivElement>) => {
    dragging.current = false;
    (e.currentTarget as HTMLElement).releasePointerCapture(e.pointerId);
  };

  return (
    <div
      ref={viewportRef}
      className="relative h-full rounded-2xl border border-slate-200 bg-white overflow-hidden"
      style={{ touchAction: "none" }}
      onPointerDown={onPointerDown}
      onPointerMove={onPointerMove}
      onPointerUp={onPointerUp}
    >
      {error ? (
        <div className="p-4 text-sm text-red-600">{error}</div>
      ) : !svgUrl ? (
        <div className="p-4 text-sm text-slate-500">2D çizim hazırlanıyor...</div>
      ) : (
        <div className="absolute inset-0 flex items-center justify-center">
          <div
            className="origin-center"
            style={{ transform: `translate(${offset.x}px, ${offset.y}px) scale(${scale})` }}
          >
            <img src={svgUrl} alt="DXF preview" className="max-w-none" />
          </div>
        </div>
      )}

      {manifest && layerList.length > 0 ? (
        <div className="absolute right-3 top-3 max-h-[45%] w-[220px] overflow-auto rounded-lg border border-slate-200 bg-white/95 p-2 text-xs">
          <div className="mb-1 flex items-center justify-between gap-2">
            <div className="font-semibold text-slate-900">Katmanlar</div>
            <button
              type="button"
              className="rounded border border-slate-300 bg-white px-1.5 py-0.5 text-[10px] text-slate-600"
              onClick={resetFit}
            >
              Fit
            </button>
          </div>
          <div className="space-y-1.5">
            {layerList.map((layer) => (
              <label key={layer.name} className="flex items-center gap-2 text-slate-700">
                <input
                  type="checkbox"
                  checked={activeLayers.has(layer.name)}
                  onChange={(e) => {
                    const next = new Set(activeLayers);
                    if (e.target.checked) next.add(layer.name);
                    else next.delete(layer.name);
                    setActiveLayers(next);
                  }}
                />
                <span className="h-2 w-2 rounded-full" style={{ backgroundColor: layer.color }} />
                <span className="truncate" title={layer.name}>
                  {layer.name}
                </span>
              </label>
            ))}
          </div>
        </div>
      ) : null}
    </div>
  );
}
