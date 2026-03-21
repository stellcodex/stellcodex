"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { DxfManifest, getDxfManifest, getDxfRender } from "@/services/api";

type DxfViewerProps = {
  fileId: string;
  fitRequestKey?: number;
  background?: "dark" | "light";
  showLayers?: boolean;
  className?: string;
  onSvgUrlChange?: (url: string | null) => void;
  onStatusChange?: (state: { ready: boolean; error: string | null }) => void;
};

export function DxfViewer({
  fileId,
  fitRequestKey = 0,
  background = "dark",
  showLayers = true,
  className,
  onSvgUrlChange,
  onStatusChange,
}: DxfViewerProps) {
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
  const bbox = useMemo(() => manifest?.bbox ?? null, [manifest]);

  const isPendingError = (value: string) => {
    const msg = value.toLowerCase();
    return msg.includes("not ready") || msg.includes("processing") || msg.includes("preparing");
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
          const preferred = data.layers.filter((l) => l.is_visible).map((l) => l.name);
          const initial = new Set((preferred.length > 0 ? preferred : data.layers.map((l) => l.name)));
          setActiveLayers(initial);
        }
        manifestLoadedRef.current = true;
        setError(null);
      } catch (e: any) {
        if (cancelled) return;
        const message = e?.message || "The DXF manifest could not be loaded.";
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
        const message = e?.message || "DXF rendering failed.";
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
    onSvgUrlChange?.(svgUrl);
  }, [onSvgUrlChange, svgUrl]);

  useEffect(() => {
    onStatusChange?.({ ready: Boolean(svgUrl), error });
  }, [error, onStatusChange, svgUrl]);

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

  const fitToBounds = useCallback(() => {
    const host = viewportRef.current;
    if (!host || !bbox) {
      setScale(1);
      setOffset({ x: 0, y: 0 });
      return;
    }
    const hostW = host.clientWidth || 1;
    const hostH = host.clientHeight || 1;
    const drawW = Math.max(1, bbox.max_x - bbox.min_x);
    const drawH = Math.max(1, bbox.max_y - bbox.min_y);
    const fit = Math.max(0.2, Math.min(10, Math.min(hostW / drawW, hostH / drawH) * 0.92));
    setScale(fit);
    setOffset({ x: 0, y: 0 });
  }, [bbox]);

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

  useEffect(() => {
    if (!manifest || !svgUrl) return;
    fitToBounds();
  }, [manifest, svgUrl, fitToBounds]);

  useEffect(() => {
    if (!manifest) return;
    fitToBounds();
  }, [fitRequestKey, fitToBounds, manifest]);

  const resetFit = () => fitToBounds();

  const isDark = background === "dark";

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
      className={[
        "relative h-full overflow-hidden rounded-2xl border",
        isDark ? "border-slate-800 bg-[#07111f]" : "border-slate-200 bg-white",
        className || "",
      ].join(" ")}
      style={{ touchAction: "none" }}
      onPointerDown={onPointerDown}
      onPointerMove={onPointerMove}
      onPointerUp={onPointerUp}
    >
      {error ? (
        <div className={`p-4 text-sm ${isDark ? "text-red-200" : "text-red-600"}`}>{error}</div>
      ) : !svgUrl ? (
        <div className={`p-4 text-sm ${isDark ? "text-slate-300" : "text-slate-500"}`}>
          {manifest && activeLayers.size === 0 ? "No visible layer is selected." : "Preparing 2D drawing..."}
        </div>
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

      {showLayers && manifest && layerList.length > 0 ? (
        <div
          className={[
            "absolute right-3 top-3 max-h-[45%] w-[220px] overflow-auto rounded-lg border p-2 text-xs",
            isDark ? "border-slate-700 bg-slate-950/92 text-slate-100" : "border-slate-200 bg-white/95 text-slate-700",
          ].join(" ")}
        >
          <div className="mb-1 flex items-center justify-between gap-2">
            <div className={`font-semibold ${isDark ? "text-white" : "text-slate-900"}`}>Layers</div>
            <button
              type="button"
              className={[
                "rounded border px-1.5 py-0.5 text-[10px]",
                isDark ? "border-slate-700 bg-slate-900 text-slate-200" : "border-slate-300 bg-white text-slate-600",
              ].join(" ")}
              onClick={resetFit}
            >
              Fit
            </button>
          </div>
          <div className="space-y-1.5">
            {layerList.map((layer) => (
              <label key={layer.name} className={`flex items-center gap-2 ${isDark ? "text-slate-200" : "text-slate-700"}`}>
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
                <span className="h-2 w-2 rounded-full border border-black/15" style={{ backgroundColor: layer.color }} />
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
