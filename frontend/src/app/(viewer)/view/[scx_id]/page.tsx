"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { PrimaryButton } from "@/components/ui/PrimaryButton";
import { SecondaryButton } from "@/components/ui/SecondaryButton";
import { Card } from "@/components/ui/Card";
import { Container } from "@/components/ui/Container";
import { StatusPill } from "@/components/ui/StatusPill";
import { EmptyState } from "@/components/ui/EmptyState";
import { tokens } from "@/lib/tokens";
import { SCX_ID_REGEX } from "@/data/system-constants";
import { DxfViewer } from "@/components/viewer/DxfViewer";
import { ThreeViewer, RenderMode, ProjectionMode, ViewerNode } from "@/components/viewer/ThreeViewer";
import { CAMERA_PRESETS, QUALITY_DEFAULT, QUALITY_TO_LOD, QualityLevel, VIEWER_MODE_LABEL, VIEWER_MODE_ORDER } from "@/components/viewer/viewer-quality-config";
import { createShare, downloadScx, fetchAuthedBlobUrl, getFile, getFileStatus, FileDetail } from "@/services/api";

const STATUS_POLL_MS = 1500;

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
  const [statusInfo, setStatusInfo] = useState<{ state: string; progress_hint?: string | null } | null>(null);
  const [blobUrl, setBlobUrl] = useState<string | null>(null);
  const [contentType, setContentType] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [retryTick, setRetryTick] = useState(0);
  const [renderMode, setRenderMode] = useState<RenderMode>("shadedEdges");
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
  const [quality, setQuality] = useState<QualityLevel>(QUALITY_DEFAULT);
  const [cameraPreset, setCameraPreset] = useState<"iso" | "front" | "top" | "right">("iso");
  const [leftTab, setLeftTab] = useState<"assembly" | "display" | "section">("assembly");
  const [bottomTab, setBottomTab] = useState<"section" | "explode" | "quality">("quality");
  const [treeQuery, setTreeQuery] = useState("");
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

  const resolveTarget3dUrl = useCallback((f: FileDetail, qualityLevel: QualityLevel) => {
    const lods = f.lods || {};
    const preferred = QUALITY_TO_LOD[qualityLevel];
    const ordered = [preferred, "lod2", "lod1", "lod0"] as const;
    for (const lod of ordered) {
      const candidate = lods[lod]?.url;
      if (typeof candidate === "string" && candidate.length > 0) return candidate;
    }
    return f.gltf_url || null;
  }, []);

  useEffect(() => {
    if (!fileId || !SCX_ID_REGEX.test(fileId)) {
      setError("Geçersiz dosya kimliği. Yeniden yükleyin.");
      return;
    }
    let cancelled = false;
    let timeoutId: ReturnType<typeof setTimeout> | null = null;
    const schedule = () => {
      if (timeoutId) clearTimeout(timeoutId);
      timeoutId = setTimeout(load, STATUS_POLL_MS);
    };
    const load = async () => {
      try {
        setLoading(true);
        const status = await getFileStatus(fileId);
        if (cancelled) return;
        setStatusInfo(status);
        setError(null);
        if (status.state === "failed") {
          setProcessing(false);
          setLoading(false);
          setError("Donusturme basarisiz. Tekrar deneyin.");
          return;
        }
        if (status.state !== "succeeded") {
          setProcessing(true);
          setLoading(false);
          schedule();
          return;
        }

        const f = await getFile(fileId);
        if (cancelled) return;
        setFile(f);
        if (f.quality_default && ["Ultra", "High", "Medium", "Low"].includes(f.quality_default)) {
          setQuality(f.quality_default as QualityLevel);
        }
        setLoading(false);
        setProcessing(false);
        if (is2dFile(f)) {
          setContentType(f.content_type);
          if (f.original_filename.toLowerCase().endsWith(".dxf")) {
            lastResolvedUrlRef.current = null;
            setBlobUrl(null);
            return;
          }
          if (!f.original_url) {
            setError("2D içerik hazır değil. Lütfen tekrar deneyin.");
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
        const target3dUrl = resolveTarget3dUrl(f, quality);
        if (!target3dUrl) {
          setError("3D içerik hazır değil. Lütfen tekrar deneyin.");
          return;
        }
        if (lastResolvedUrlRef.current === target3dUrl && objectUrlRef.current) {
          setBlobUrl(objectUrlRef.current);
          return;
        }
        if (objectUrlRef.current) {
          URL.revokeObjectURL(objectUrlRef.current);
          objectUrlRef.current = null;
        }
        const url = await fetchAuthedBlobUrl(target3dUrl);
        objectUrlRef.current = url;
        lastResolvedUrlRef.current = target3dUrl;
        setBlobUrl(url);
      } catch (e: any) {
        if (!cancelled) {
          setLoading(false);
          setError((e?.message || "Dosya yüklenemedi") + ". Tekrar deneyin.");
        }
      }
    };
    void load();
    return () => {
      cancelled = true;
      if (timeoutId) clearTimeout(timeoutId);
      if (objectUrlRef.current) {
        URL.revokeObjectURL(objectUrlRef.current);
        objectUrlRef.current = null;
      }
      lastResolvedUrlRef.current = null;
    };
  }, [fileId, retryTick, quality, resolveTarget3dUrl]);

  const handleShare = async () => {
    if (!fileId) return;
    setShareBusy(true);
    setShareError(null);
    try {
      const res = await createShare(fileId);
      const link = `${window.location.origin}/share/${res.token}`;
      setShareLink(link);
    } catch (e: any) {
      setShareError((e?.message || "Paylaşım oluşturulamadı") + ". Tekrar deneyin.");
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

  const handleDownloadScx = async () => {
    if (!fileId) return;
    try {
      const blob = await downloadScx(fileId);
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `${fileId}.scx`;
      a.click();
      URL.revokeObjectURL(url);
    } catch (e: any) {
      setError(e?.message || "SCX indirilemedi.");
    }
  };

  const filteredNodes = useMemo(() => {
    const q = treeQuery.trim().toLowerCase();
    if (!q) return nodes;
    return nodes.filter((n) => n.name.toLowerCase().includes(q));
  }, [nodes, treeQuery]);

  const viewerBody = useMemo(() => {
    if (!fileId) {
      return (
        <EmptyState
          title="Dosya bulunamadı"
          description="Dosya bulunamadı. Yeni yükleme yapın."
          action={<SecondaryButton href="/upload">Yükleme ekranına git</SecondaryButton>}
        />
      );
    }
    if (error) {
      return (
        <EmptyState
          title="İşlem başarısız"
          description={error}
          action={
            <div className="flex flex-wrap items-center gap-2">
              <SecondaryButton onClick={() => setRetryTick((t) => t + 1)}>Tekrar dene</SecondaryButton>
              <PrimaryButton href="/account">Yöneticiye ulaş</PrimaryButton>
            </div>
          }
        />
      );
    }
    if (is2d && file?.original_filename.toLowerCase().endsWith(".dxf")) {
      return (
        <div className="h-[70vh] overflow-hidden rounded-2xl border border-[#e5e7eb] bg-white p-4">
          <DxfViewer fileId={fileId} />
        </div>
      );
    }

    if (loading || processing || !blobUrl) {
      const statusRaw = (statusInfo?.state || "running").toLowerCase();
      const status = statusRaw === "failed" ? "failed" : statusRaw === "succeeded" ? "ready" : statusRaw === "queued" ? "queued" : "running";
      const statusLabel = statusInfo?.progress_hint
        ? `İşleniyor… (${statusInfo.progress_hint})`
        : "İşleniyor…";
      return (
        <Card className="p-5">
          <div className="mb-4 flex items-center gap-3">
            <StatusPill status={status} label={statusLabel} />
            <span style={tokens.typography.body} className="text-[#6b7280]">Görüntüleme hazırlanıyor…</span>
          </div>
          <div className="h-[60vh] w-full animate-pulse rounded-xl bg-[#e6e2d8]" />
          <div className="mt-4 flex items-center justify-between text-xs text-[#6b7280]">
            <span>Durum güncelleniyor…</span>
            <SecondaryButton href="/dashboard">Durumu gör</SecondaryButton>
          </div>
        </Card>
      );
    }

    if (is2d) {
      return (
        <div className="h-[70vh] overflow-hidden rounded-2xl border border-[#e5e7eb] bg-white p-4">
          {contentType === "application/pdf" ? (
            <div className="flex h-full flex-col gap-3">
              <div className="flex items-center gap-2 text-xs text-[#6b7280]">
                <span>Sayfa</span>
                <input
                  type="number"
                  min={1}
                  value={pdfPage}
                  onChange={(e) => setPdfPage(Number(e.target.value) || 1)}
                  className="h-8 w-20 rounded-lg border border-[#d1d5db] bg-white px-2 text-sm text-[#111827]"
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
      <Card className="h-[70vh] overflow-hidden">
        <div ref={viewRef} className="h-full">
          <ThreeViewer
            url={blobUrl}
            renderMode={renderMode}
            projection={projection}
            cameraPreset={cameraPreset}
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
      </Card>
    );
  }, [fileId, error, processing, blobUrl, is2d, file, statusInfo, contentType, pdfPage, renderMode, projection, clip, clipOffset, hiddenNodes, selected, measureEnabled]);

  return (
    <main className="py-6 sm:py-8">
      <Container>
        <div className="mb-4 flex items-center justify-between gap-3">
          <div className="flex items-center gap-3">
            <SecondaryButton href="/dashboard">Geri</SecondaryButton>
            <div style={tokens.typography.body} className="text-[#6b7280]">
              {file ? shortName(file.original_filename) : "Görüntüleyici"}
            </div>
          </div>
          <div className="flex items-center gap-2">
            <SecondaryButton onClick={() => setShareOpen((v) => !v)}>Paylaş</SecondaryButton>
            <PrimaryButton onClick={toggleFullscreen}>Tam ekran</PrimaryButton>
          </div>
        </div>

        <div className="grid gap-4 lg:grid-cols-[280px_1fr_64px]">
          <Card className="p-3">
            <div className="grid grid-cols-3 gap-1 rounded-lg border border-[#d1d5db] bg-[#f8f8f8] p-1 text-[11px]">
              <button className={`rounded px-1 py-1 ${leftTab === "assembly" ? "bg-white font-semibold" : ""}`} onClick={() => setLeftTab("assembly")}>Assembly Tree</button>
              <button className={`rounded px-1 py-1 ${leftTab === "display" ? "bg-white font-semibold" : ""}`} onClick={() => setLeftTab("display")}>View/Display</button>
              <button className={`rounded px-1 py-1 ${leftTab === "section" ? "bg-white font-semibold" : ""}`} onClick={() => setLeftTab("section")}>Section</button>
            </div>

            {leftTab === "assembly" ? (
              <div className="mt-3">
                <input
                  value={treeQuery}
                  onChange={(e) => setTreeQuery(e.target.value)}
                  placeholder="Ağaçta ara..."
                  className="h-8 w-full rounded-lg border border-[#d1d5db] bg-white px-2 text-xs"
                />
                <div className="mt-2 max-h-[56vh] overflow-auto text-xs text-[#374151]">
                  {filteredNodes.length === 0 ? (
                    <div className="text-[#8a9895]">Düğüm bulunamadı.</div>
                  ) : (
                    filteredNodes.map((n) => (
                      <div key={n.id} className="flex items-center justify-between gap-2 py-1">
                        <button className="truncate text-left hover:text-[#111827]" onClick={() => setSelected(n)}>
                          {n.name}
                        </button>
                        <button
                          className="rounded border border-[#d1d5db] px-2 py-0.5 text-[10px]"
                          onClick={() => {
                            const next = new Set(hiddenNodes);
                            if (next.has(n.id)) next.delete(n.id);
                            else next.add(n.id);
                            setHiddenNodes(next);
                          }}
                        >
                          {hiddenNodes.has(n.id) ? "Göster" : "Gizle"}
                        </button>
                      </div>
                    ))
                  )}
                </div>
              </div>
            ) : null}

            {leftTab === "display" ? (
              <div className="mt-3 grid gap-3 text-xs">
                <div className="font-semibold text-[#111827]">Görünüm modu</div>
                <div className="grid gap-2">
                  {VIEWER_MODE_ORDER.map((mode) => (
                    <button
                      key={mode}
                      className={`rounded-lg border px-2 py-1 text-left ${
                        renderMode === mode ? "border-[#111827] bg-[#111827] text-white" : "border-[#d1d5db] bg-white text-[#374151]"
                      }`}
                      onClick={() => setRenderMode(mode)}
                    >
                      {VIEWER_MODE_LABEL[mode]}
                    </button>
                  ))}
                </div>
                <div className="font-semibold text-[#111827]">Projeksiyon</div>
                <div className="grid grid-cols-2 gap-2">
                  {(["perspective", "orthographic"] as ProjectionMode[]).map((mode) => (
                    <button
                      key={mode}
                      className={`rounded-lg border px-2 py-1 ${
                        projection === mode ? "border-[#111827] bg-[#111827] text-white" : "border-[#d1d5db] bg-white text-[#374151]"
                      }`}
                      onClick={() => setProjection(mode)}
                    >
                      {mode === "perspective" ? "Persp" : "Ortho"}
                    </button>
                  ))}
                </div>
              </div>
            ) : null}

            {leftTab === "section" ? (
              <div className="mt-3 grid gap-3 text-xs">
                <label className="flex items-center justify-between">
                  Kesit aktif
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
                <div className="text-[11px] text-[#6b7280]">X/Y/Z ve serbest düzlem ayarları bu panelde genişletilecek.</div>
              </div>
            ) : null}
          </Card>

          <div className="grid gap-3">
            <Card className="p-3">
              <div className="flex flex-wrap items-center justify-between gap-2">
                <div className="flex flex-wrap items-center gap-2">
                  {CAMERA_PRESETS.map((preset) => (
                    <button
                      key={preset.key}
                      className={`rounded-lg border px-3 py-1 text-xs ${
                        cameraPreset === preset.key ? "border-[#111827] bg-[#111827] text-white" : "border-[#d1d5db] bg-white text-[#374151]"
                      }`}
                      onClick={() => setCameraPreset(preset.key)}
                    >
                      {preset.label}
                    </button>
                  ))}
                </div>
                <div className="flex items-center gap-2">
                  <button className="rounded-lg border border-[#d1d5db] bg-white px-2 py-1 text-xs" onClick={() => setCameraPreset("iso")}>Home</button>
                  <button className="rounded-lg border border-[#d1d5db] bg-white px-2 py-1 text-xs" onClick={handleScreenshot}>Screenshot</button>
                  <button className="rounded-lg border border-[#d1d5db] bg-white px-2 py-1 text-xs" onClick={handleDownloadScx}>Download .scx</button>
                </div>
              </div>
            </Card>

            {viewerBody}

            {!is2d ? (
              <Card className="p-3">
                <div className="mb-2 grid grid-cols-3 gap-2 text-xs">
                  <button className={`rounded border px-2 py-1 ${bottomTab === "section" ? "border-[#111827] bg-[#111827] text-white" : "border-[#d1d5db] bg-white"}`} onClick={() => setBottomTab("section")}>Section</button>
                  <button className={`rounded border px-2 py-1 ${bottomTab === "explode" ? "border-[#111827] bg-[#111827] text-white" : "border-[#d1d5db] bg-white"}`} onClick={() => setBottomTab("explode")}>Explode</button>
                  <button className={`rounded border px-2 py-1 ${bottomTab === "quality" ? "border-[#111827] bg-[#111827] text-white" : "border-[#d1d5db] bg-white"}`} onClick={() => setBottomTab("quality")}>Quality</button>
                </div>
                {bottomTab === "section" ? (
                  <div className="text-xs text-[#374151]">Çoklu düzlem section ayarları burada toplanır.</div>
                ) : null}
                {bottomTab === "explode" ? (
                  <div className="text-xs text-[#374151]">Auto explode/axis explode kontrolü bu panelde genişletilecek.</div>
                ) : null}
                {bottomTab === "quality" ? (
                  <div className="grid gap-2 text-xs">
                    <div className="text-[#6b7280]">Varsayılan kalite: maksimum (Ultra)</div>
                    <div className="grid grid-cols-4 gap-2">
                      {(["Ultra", "High", "Medium", "Low"] as QualityLevel[]).map((lvl) => (
                        <button
                          key={lvl}
                          onClick={() => setQuality(lvl)}
                          className={`rounded border px-2 py-1 ${quality === lvl ? "border-[#111827] bg-[#111827] text-white" : "border-[#d1d5db] bg-white text-[#374151]"}`}
                        >
                          {lvl}
                        </button>
                      ))}
                    </div>
                    <div className="text-[11px] text-[#6b7280]">Offline render viewer modu değildir; ayrı render job hattı kullanılır.</div>
                  </div>
                ) : null}
              </Card>
            ) : null}
          </div>

          <Card className="p-2">
            <div className="grid gap-2">
              <button className="rounded border border-[#d1d5db] px-2 py-2 text-xs" onClick={() => setCameraPreset("iso")}>Orbit</button>
              <button className="rounded border border-[#d1d5db] px-2 py-2 text-xs">Pan</button>
              <button className="rounded border border-[#d1d5db] px-2 py-2 text-xs">Zoom +</button>
              <button className="rounded border border-[#d1d5db] px-2 py-2 text-xs">Zoom -</button>
              <button className="rounded border border-[#d1d5db] px-2 py-2 text-xs" onClick={() => setCameraPreset("iso")}>Fit</button>
              <button className={`rounded border px-2 py-2 text-xs ${clip ? "border-[#111827] bg-[#111827] text-white" : "border-[#d1d5db]"}`} onClick={() => setClip((v) => !v)}>Section</button>
              <button className="rounded border border-[#d1d5db] px-2 py-2 text-xs" onClick={() => setBottomTab("explode")}>Explode</button>
            </div>
          </Card>
        </div>

        {shareOpen ? (
          <Card className="mt-6 p-5">
            <div className="text-sm font-semibold text-[#111827]">Paylaş</div>
            <p className="mt-1 text-xs text-[#6b7280]">Varsayılan izin: sadece görüntüleme.</p>
            <div className="mt-3 flex flex-wrap items-center gap-2">
              <PrimaryButton onClick={handleShare} disabled={shareBusy}>Link oluştur</PrimaryButton>
              {shareLink ? (
                <div className="flex flex-wrap items-center gap-2">
                  <input readOnly value={shareLink} className="h-9 w-[320px] rounded-lg border border-[#d1d5db] bg-white px-2 text-xs" />
                  <SecondaryButton onClick={handleCopy}>Kopyala</SecondaryButton>
                </div>
              ) : null}
            </div>
            {shareError ? <div className="mt-2 text-xs text-red-600">{shareError}</div> : null}
            <button className="mt-4 text-xs font-semibold text-[#374151]" onClick={() => setAdvancedOpen((v) => !v)}>Gelişmiş</button>
            {advancedOpen ? (
              <div className="mt-3 grid gap-2 text-xs text-[#6b7280]">
                <label className="flex items-center gap-2"><input type="checkbox" disabled />Yorumlar (V1 kapalı)</label>
                <label className="flex items-center gap-2"><input type="checkbox" disabled />İndirme (V1 kapalı)</label>
                <label className="flex items-center gap-2">Süre (V1 kapalı)<input type="number" disabled className="h-8 w-20 rounded border border-[#d1d5db] px-2" /></label>
              </div>
            ) : null}
          </Card>
        ) : null}
      </Container>
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
