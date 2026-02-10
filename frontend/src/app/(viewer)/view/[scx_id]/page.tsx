"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { Button } from "@/components/ui/Button";
import { DxfViewer } from "@/components/viewer/DxfViewer";
import { ThreeViewer, RenderMode, ProjectionMode, ViewerNode } from "@/components/viewer/ThreeViewer";
import { createShare, fetchAuthedBlobUrl, getFile, FileDetail } from "@/services/api";

const STATUS_POLL_MS = 4000;

function is2dFile(file: FileDetail) {
  const lower = file.original_filename.toLowerCase();
  if (file.content_type === "application/pdf") return true;
  if (file.content_type.startsWith("image/")) return true;
  return lower.endsWith(".dxf");
}

function shortName(name: string) {
  if (name.length <= 32) return name;
  return name.slice(0, 16) + "..." + name.slice(-12);
}

export default function ViewPage() {
  const params = useParams();
  const router = useRouter();
  const fileId = typeof params.scx_id === "string" ? params.scx_id : "";
  const [file, setFile] = useState<FileDetail | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [processing, setProcessing] = useState(false);
  const [blobUrl, setBlobUrl] = useState<string | null>(null);
  const [contentType, setContentType] = useState<string | null>(null);
  const [renderMode, setRenderMode] = useState<RenderMode>("shaded");
  const [projection, setProjection] = useState<ProjectionMode>("perspective");
  const [clip, setClip] = useState(false);
  const [clipOffset, setClipOffset] = useState(0);
  const [nodes, setNodes] = useState<ViewerNode[]>([]);
  const [hiddenNodes, setHiddenNodes] = useState<Set<string>>(new Set());
  const [selected, setSelected] = useState<ViewerNode | null>(null);
  const [measureEnabled, setMeasureEnabled] = useState(false);
  const [measureValue, setMeasureValue] = useState<number | null>(null);
  const [shareOpen, setShareOpen] = useState(false);
  const [shareLink, setShareLink] = useState<string | null>(null);
  const [shareBusy, setShareBusy] = useState(false);
  const [shareError, setShareError] = useState<string | null>(null);
  const [advancedOpen, setAdvancedOpen] = useState(false);
  const [pdfPage, setPdfPage] = useState(1);
  const screenshotRef = useRef<(() => string | null) | null>(null);
  const viewRef = useRef<HTMLDivElement | null>(null);
  const objectUrlRef = useRef<string | null>(null);
  const lastResolvedUrlRef = useRef<string | null>(null);

  const is2d = file ? is2dFile(file) : false;

  const handleNodes = useCallback((next: ViewerNode[]) => {
    setNodes(next);
  }, []);

  const handleSelect = useCallback((node: ViewerNode | null) => {
    setSelected(node);
  }, []);

  const handleMeasure = useCallback((dist: number | null) => {
    setMeasureValue(dist);
  }, []);

  const handleScreenshotReady = useCallback((fn: () => string | null) => {
    screenshotRef.current = fn;
  }, []);

  useEffect(() => {
    if (!fileId) {
      setError("Dosya bulunamadi. Yeniden yukleyin.");
      return;
    }
    let cancelled = false;
    const load = async () => {
      try {
        const f = await getFile(fileId);
        if (cancelled) return;
        setFile(f);
        setError(null);
        if (f.status === "failed") {
          setProcessing(false);
          setError((f.error || "Donusturme basarisiz") + ". Tekrar deneyin.");
          return;
        }
        if (f.status !== "ready") {
          setProcessing(true);
          return;
        }
        setProcessing(false);
        if (is2dFile(f)) {
          setContentType(f.content_type);
          if (f.original_filename.toLowerCase().endsWith(".dxf")) {
            lastResolvedUrlRef.current = null;
            setBlobUrl(null);
            return;
          }
          if (!f.original_url) {
            setError("2D icerik hazir degil. Lutfen tekrar deneyin.");
            return;
          }
          if (lastResolvedUrlRef.current === f.original_url && objectUrlRef.current) {
            setBlobUrl(objectUrlRef.current);
            return;
          }
          if (objectUrlRef.current) {
            URL.revokeObjectURL(objectUrlRef.current);
            objectUrlRef.current = null;
          }
          const url = await fetchAuthedBlobUrl(f.original_url);
          objectUrlRef.current = url;
          lastResolvedUrlRef.current = f.original_url;
          setBlobUrl(url);
          return;
        }
        if (!f.gltf_url) {
          setError("3D icerik hazir degil. Lutfen tekrar deneyin.");
          return;
        }
        if (lastResolvedUrlRef.current === f.gltf_url && objectUrlRef.current) {
          setBlobUrl(objectUrlRef.current);
          return;
        }
        if (objectUrlRef.current) {
          URL.revokeObjectURL(objectUrlRef.current);
          objectUrlRef.current = null;
        }
        const url = await fetchAuthedBlobUrl(f.gltf_url);
        objectUrlRef.current = url;
        lastResolvedUrlRef.current = f.gltf_url;
        setBlobUrl(url);
      } catch (e: any) {
        if (!cancelled) setError((e?.message || "Dosya yuklenemedi") + ". Tekrar deneyin.");
      }
    };
    void load();
    const id = setInterval(load, STATUS_POLL_MS);
    return () => {
      cancelled = true;
      clearInterval(id);
      if (objectUrlRef.current) {
        URL.revokeObjectURL(objectUrlRef.current);
        objectUrlRef.current = null;
      }
      lastResolvedUrlRef.current = null;
    };
  }, [fileId]);

  const handleShare = async () => {
    if (!fileId) return;
    setShareBusy(true);
    setShareError(null);
    try {
      const res = await createShare(fileId);
      const link = `${window.location.origin}/share/${res.token}`;
      setShareLink(link);
    } catch (e: any) {
      setShareError((e?.message || "Paylasim olusturulamadi") + ". Tekrar deneyin.");
    } finally {
      setShareBusy(false);
    }
  };

  const handleCopy = async () => {
    if (!shareLink) return;
    try {
      await navigator.clipboard.writeText(shareLink);
    } catch {
      // ignore
    }
  };

  const toggleFullscreen = async () => {
    if (!viewRef.current) return;
    if (!document.fullscreenElement) {
      await viewRef.current.requestFullscreen();
    } else {
      await document.exitFullscreen();
    }
  };

  const handleScreenshot = () => {
    const data = screenshotRef.current?.();
    if (!data) return;
    const a = document.createElement("a");
    a.href = data;
    a.download = `stellcodex-${fileId}.png`;
    a.click();
  };

  const viewerBody = useMemo(() => {
    if (!fileId) {
      return (
        <div className="rounded-2xl border border-[#d7d3c8] bg-white/80 p-6 text-center">
          <div className="text-2xl">⭘</div>
          <div className="mt-2 text-sm text-[#2c4b49]">Dosya bulunamadi. Yeni yukleme yapin.</div>
          <div className="mt-4">
            <Button href="/upload" variant="secondary">Yukleme ekranina git</Button>
          </div>
        </div>
      );
    }
    if (error) {
      return (
        <div className="rounded-2xl border border-[#d7d3c8] bg-white/80 p-6 text-center">
          <div className="text-2xl">⭘</div>
          <div className="mt-2 text-sm text-[#2c4b49]">{error}</div>
          <div className="mt-4">
            <Button href="/upload" variant="secondary">Yeni dosya yukle</Button>
          </div>
        </div>
      );
    }
    if (is2d && file?.original_filename.toLowerCase().endsWith(".dxf")) {
      return (
        <div className="h-[70vh] overflow-hidden rounded-2xl border border-[#d7d3c8] bg-white/80 p-4">
          <DxfViewer fileId={fileId} />
        </div>
      );
    }

    if (processing || !blobUrl) {
      return (
        <div className="rounded-2xl border border-[#d7d3c8] bg-white/80 p-6 text-center">
          <div className="text-2xl">⭘</div>
          <div className="mt-2 text-sm text-[#2c4b49]">Dosya isleniyor. Birazdan goruntulenecek.</div>
          <div className="mt-4">
            <Button href="/dashboard" variant="secondary">Durumu gor</Button>
          </div>
        </div>
      );
    }

    if (is2d) {
      return (
        <div className="h-[70vh] overflow-hidden rounded-2xl border border-[#d7d3c8] bg-white/80 p-4">
          {contentType === "application/pdf" ? (
            <div className="flex h-full flex-col gap-3">
              <div className="flex items-center gap-2 text-xs text-[#4f6f6b]">
                <span>Page</span>
                <input
                  type="number"
                  min={1}
                  value={pdfPage}
                  onChange={(e) => setPdfPage(Number(e.target.value) || 1)}
                  className="h-8 w-20 rounded-lg border border-[#d7d3c8] bg-white px-2 text-sm text-[#0c2a2a]"
                />
              </div>
              <iframe src={`${blobUrl}#page=${pdfPage}`} className="h-full w-full rounded-xl" />
            </div>
          ) : (
            <PanZoomImage src={blobUrl} />
          )}
        </div>
      );
    }

    return (
      <div ref={viewRef} className="h-[70vh] overflow-hidden rounded-2xl border border-[#d7d3c8] bg-white/80">
        <ThreeViewer
          url={blobUrl}
          renderMode={renderMode}
          projection={projection}
          clip={clip}
          clipOffset={clipOffset}
          hiddenNodes={hiddenNodes}
          selectedId={selected?.id ?? null}
          measureEnabled={measureEnabled}
          onNodes={handleNodes}
          onSelect={handleSelect}
          onMeasure={handleMeasure}
          onScreenshotReady={handleScreenshotReady}
        />
      </div>
    );
  }, [fileId, error, processing, blobUrl, is2d, file, contentType, pdfPage, renderMode, projection, clip, clipOffset, hiddenNodes, selected, measureEnabled]);

  return (
    <main className="mx-auto max-w-6xl px-6 pb-16 pt-10">
      <div className="mb-4 flex items-center justify-between gap-3">
        <div className="flex items-center gap-3">
          <Button href="/dashboard" variant="secondary">Back</Button>
          <div className="text-sm text-[#4f6f6b]">{file ? shortName(file.original_filename) : "Viewer"}</div>
        </div>
        <div className="flex items-center gap-2">
          <Button onClick={() => setShareOpen((v) => !v)} variant="secondary">Share</Button>
          <Button onClick={toggleFullscreen}>Fullscreen</Button>
        </div>
      </div>

      <div className="grid gap-4 lg:grid-cols-[1fr_260px]">
        {viewerBody}

        <aside className="rounded-2xl border border-[#d7d3c8] bg-white/80 p-4">
          <div className="text-xs font-semibold uppercase tracking-[0.18em] text-[#4f6f6b]">Tools</div>

          {!is2d ? (
            <div className="mt-4 grid gap-3 text-sm">
              <div>
                <div className="text-xs font-semibold text-[#0c2a2a]">Render</div>
                <div className="mt-2 grid grid-cols-3 gap-2">
                  {(["shaded", "wireframe", "hidden"] as RenderMode[]).map((mode) => (
                    <button
                      key={mode}
                      className={`rounded-lg border px-2 py-1 text-xs ${
                        renderMode === mode
                          ? "border-[#0c3b3a] bg-[#0c3b3a] text-white"
                          : "border-[#d7d3c8] bg-white text-[#2c4b49]"
                      }`}
                      onClick={() => setRenderMode(mode)}
                    >
                      {mode}
                    </button>
                  ))}
                </div>
              </div>

              <div>
                <div className="text-xs font-semibold text-[#0c2a2a]">Projection</div>
                <div className="mt-2 grid grid-cols-2 gap-2">
                  {(["perspective", "orthographic"] as ProjectionMode[]).map((mode) => (
                    <button
                      key={mode}
                      className={`rounded-lg border px-2 py-1 text-xs ${
                        projection === mode
                          ? "border-[#0c3b3a] bg-[#0c3b3a] text-white"
                          : "border-[#d7d3c8] bg-white text-[#2c4b49]"
                      }`}
                      onClick={() => setProjection(mode)}
                    >
                      {mode}
                    </button>
                  ))}
                </div>
              </div>

              <label className="flex items-center justify-between text-xs text-[#2c4b49]">
                Section plane
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

              <label className="flex items-center justify-between text-xs text-[#2c4b49]">
                Measure
                <input type="checkbox" checked={measureEnabled} onChange={(e) => setMeasureEnabled(e.target.checked)} />
              </label>
              {measureEnabled ? (
                <div className="text-xs text-[#4f6f6b]">
                  {measureValue ? `Distance: ${measureValue.toFixed(2)}` : "Iki nokta secin"}
                </div>
              ) : null}

              <div>
                <div className="text-xs font-semibold text-[#0c2a2a]">Model tree</div>
                <div className="mt-2 max-h-40 overflow-auto text-xs text-[#2c4b49]">
                  {nodes.length === 0 ? (
                    <div className="text-[#8a9895]">Node bulunamadi.</div>
                  ) : (
                    nodes.map((n) => (
                      <div key={n.id} className="flex items-center justify-between gap-2 py-1">
                        <button
                          className="text-left hover:text-[#0c2a2a]"
                          onClick={() => setSelected(n)}
                        >
                          {n.name}
                        </button>
                        <button
                          className="rounded border border-[#d7d3c8] px-2 py-0.5 text-[10px]"
                          onClick={() => {
                            const next = new Set(hiddenNodes);
                            if (next.has(n.id)) next.delete(n.id);
                            else next.add(n.id);
                            setHiddenNodes(next);
                          }}
                        >
                          {hiddenNodes.has(n.id) ? "Show" : "Hide"}
                        </button>
                      </div>
                    ))
                  )}
                </div>
              </div>

              <Button onClick={handleScreenshot} variant="secondary">
                Screenshot (PNG)
              </Button>
            </div>
          ) : (
            <div className="mt-4 text-xs text-[#2c4b49]">2D goruntuleme aktif.</div>
          )}
        </aside>
      </div>

      {shareOpen ? (
        <section className="mt-6 rounded-2xl border border-[#d7d3c8] bg-white/80 p-5">
          <div className="text-sm font-semibold text-[#0c2a2a]">Share</div>
          <p className="mt-1 text-xs text-[#4f6f6b]">Varsayilan izin: view-only.</p>

          <div className="mt-3 flex flex-wrap items-center gap-2">
            <Button onClick={handleShare} disabled={shareBusy}>Create link</Button>
            {shareLink ? (
              <div className="flex flex-wrap items-center gap-2">
                <input
                  readOnly
                  value={shareLink}
                  className="h-9 w-[320px] rounded-lg border border-[#d7d3c8] bg-white px-2 text-xs"
                />
                <Button onClick={handleCopy} variant="secondary">Copy</Button>
              </div>
            ) : null}
          </div>
          {shareError ? <div className="mt-2 text-xs text-red-600">{shareError}</div> : null}

          <button
            className="mt-4 text-xs font-semibold text-[#1d5a57]"
            onClick={() => setAdvancedOpen((v) => !v)}
          >
            Advanced
          </button>
          {advancedOpen ? (
            <div className="mt-3 grid gap-2 text-xs text-[#4f6f6b]">
              <label className="flex items-center gap-2">
                <input type="checkbox" disabled />
                Comments (V1 kapali)
              </label>
              <label className="flex items-center gap-2">
                <input type="checkbox" disabled />
                Download (V1 kapali)
              </label>
              <label className="flex items-center gap-2">
                Expiry (V1 kapali)
                <input type="number" disabled className="h-8 w-20 rounded border border-[#d7d3c8] px-2" />
              </label>
            </div>
          ) : null}
        </section>
      ) : null}
    </main>
  );
}

function PanZoomImage({ src }: { src: string }) {
  const [scale, setScale] = useState(1);
  const [offset, setOffset] = useState({ x: 0, y: 0 });
  const dragging = useRef(false);
  const lastPos = useRef({ x: 0, y: 0 });

  const onWheel = (e: React.WheelEvent<HTMLDivElement>) => {
    e.preventDefault();
    const delta = e.deltaY < 0 ? 1.1 : 0.9;
    setScale((s) => Math.min(10, Math.max(0.2, s * delta)));
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
      className="relative h-full w-full overflow-hidden rounded-xl border border-[#e3dfd3] bg-white"
      onWheel={onWheel}
      onPointerDown={onPointerDown}
      onPointerMove={onPointerMove}
      onPointerUp={onPointerUp}
    >
      <div className="absolute inset-0 flex items-center justify-center">
        <img
          src={src}
          alt="2D preview"
          className="max-w-none"
          style={{ transform: `translate(${offset.x}px, ${offset.y}px) scale(${scale})` }}
        />
      </div>
    </div>
  );
}
