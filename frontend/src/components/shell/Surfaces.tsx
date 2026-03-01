"use client";

import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { useCallback, useEffect, useMemo, useRef, useState, type ReactNode } from "react";
import { DxfViewer } from "@/components/viewer/DxfViewer";
import { RenderMode, ThreeViewer } from "@/components/viewer/ThreeViewer";
import { fetchAuthedBlobUrl, getFile, uploadDirect } from "@/services/api";
import {
  DEFAULT_PROJECT_ID,
  DEFAULT_PROJECT_NAME,
  detectWorkspaceMode,
  formatWorkspaceDate,
  getLatestWorkspaceFile,
  getWorkspaceFileById,
  registerUploadedFile,
  subscribeWorkspaceUpdates,
  type WorkspaceFileRecord,
  type WorkspaceMode,
} from "@/lib/workspace-store";
import { useShellUi } from "@/components/shell/AppShell";
import { appRegistry } from "@/data/appRegistry";

type ViewerVariant = "3d" | "2d" | "explode";
type ViewerInteractionMode = "rotate" | "pan";
type LeftPaneMode = "hidden" | "normal" | "wide";

const modeCards = appRegistry.map((item) => ({
  title: item.label,
  desc: item.description,
  href: item.href,
  icon: item.shortLabel,
}));

function useViewerMinHeight() {
  const { focusMode } = useShellUi();
  const [viewportHeight, setViewportHeight] = useState(0);

  useEffect(() => {
    const updateHeight = () => {
      setViewportHeight(window.innerHeight);
    };

    updateHeight();
    window.addEventListener("resize", updateHeight);
    return () => window.removeEventListener("resize", updateHeight);
  }, []);

  return useMemo(() => {
    if (focusMode) {
      const base = viewportHeight ? viewportHeight - 186 : 780;
      return Math.max(640, base);
    }
    const base = viewportHeight ? viewportHeight - 246 : 700;
    return Math.max(560, base);
  }, [focusMode, viewportHeight]);
}

function ViewerFrame({ minHeight, children }: { minHeight: number; children: ReactNode }) {
  const hostRef = useRef<HTMLDivElement | null>(null);
  const [height, setHeight] = useState(minHeight);

  useEffect(() => {
    setHeight((prev) => Math.max(prev, minHeight));
  }, [minHeight]);

  useEffect(() => {
    if (typeof ResizeObserver === "undefined") return;
    const host = hostRef.current;
    const parent = host?.parentElement;
    if (!host || !parent) return;

    const update = (nextHeight: number) => {
      setHeight(Math.max(minHeight, Math.floor(nextHeight)));
    };

    update(parent.getBoundingClientRect().height);

    const observer = new ResizeObserver((entries) => {
      const next = entries[0]?.contentRect.height ?? 0;
      update(next);
    });
    observer.observe(parent);

    return () => observer.disconnect();
  }, [minHeight]);

  return (
    <div ref={hostRef} className="relative w-full overflow-hidden" style={{ minHeight, height }}>
      {children}
    </div>
  );
}

function viewerLabelByVariant(variant: ViewerVariant) {
  if (variant === "2d") return "2D çizim çalışma alanı";
  if (variant === "explode") return "Patlatma çalışma alanı";
  return "3D model çalışma alanı";
}

function viewerToolsByVariant(variant: ViewerVariant) {
  if (variant === "2d") return ["Yakınlaştır", "Uzaklaştır", "Ölçü", "Not", "Katman", "Sığdır"];
  if (variant === "explode") return ["Patlat", "Topla", "Adım", "Odak", "Kesit", "Sıfırla"];
  return ["Döndür", "Kaydır", "Yakınlaştır", "Sığdır", "Kesit", "Patlat"];
}

function modeFromVariant(variant: ViewerVariant | "render"): WorkspaceMode {
  return variant === "2d" ? "2d" : "3d";
}

function appPathFromVariant(variant: ViewerVariant | "render") {
  if (variant === "2d") return "/app/2d";
  if (variant === "explode") return "/app/explode";
  if (variant === "render") return "/app/render";
  return "/app/3d";
}

function useResolvedWorkspaceFile(
  variant: ViewerVariant | "render",
  explicitFileId?: string,
  explicitFileName?: string
) {
  const searchParams = useSearchParams();
  const queryFileId = searchParams.get("file") || undefined;
  const queryFileName = searchParams.get("name") || undefined;
  const resolvedFileId = explicitFileId || queryFileId;
  const resolvedFileName = explicitFileName || queryFileName;
  const mode = modeFromVariant(variant);
  const fallbackRecord = useMemo<WorkspaceFileRecord | null>(() => {
    if (!resolvedFileId) return null;
    return {
      fileId: resolvedFileId,
      originalFilename: resolvedFileName || resolvedFileId,
      sizeBytes: 0,
      mode,
      uploadedAt: "",
      projectId: DEFAULT_PROJECT_ID,
      projectName: DEFAULT_PROJECT_NAME,
    };
  }, [mode, resolvedFileId, resolvedFileName]);
  const [selected, setSelected] = useState<WorkspaceFileRecord | null>(() => {
    if (resolvedFileId) {
      return getWorkspaceFileById(resolvedFileId) || fallbackRecord;
    }
    return getLatestWorkspaceFile(mode);
  });

  useEffect(() => {
    const refresh = () => {
      if (resolvedFileId) {
        setSelected(getWorkspaceFileById(resolvedFileId) || fallbackRecord);
        return;
      }
      setSelected(getLatestWorkspaceFile(mode));
    };

    refresh();
    return subscribeWorkspaceUpdates(refresh);
  }, [fallbackRecord, mode, resolvedFileId]);

  return selected;
}

function SelectedFileCard({
  selected,
  variant,
}: {
  selected: WorkspaceFileRecord | null;
  variant: ViewerVariant | "render";
}) {
  const targetPath = appPathFromVariant(variant);

  if (!selected) {
    return (
      <aside className="space-y-4">
        <div className="rounded-2xl border border-[#dce3ee] bg-white p-4 shadow-[0_2px_8px_rgba(15,23,42,0.06)]">
          <h3 className="text-base font-semibold text-[#0f172a]">Seçili Dosya</h3>
          <p className="mt-2 text-sm text-[#64748b]">Henüz dosya seçili değil. Dosya yükleyerek başlayın.</p>
          <div className="mt-4">
            <Link
              href="/dashboard"
              className="inline-flex h-10 items-center justify-center rounded-xl border border-[#1d4ed8] bg-[#2563eb] px-4 text-sm font-semibold text-white hover:bg-[#1d4ed8]"
            >
              Panele Git
            </Link>
          </div>
        </div>
      </aside>
    );
  }

  return (
    <aside className="space-y-4">
      <div className="rounded-2xl border border-[#dce3ee] bg-white p-4 shadow-[0_2px_8px_rgba(15,23,42,0.06)]">
        <h3 className="text-base font-semibold text-[#0f172a]">Seçili Dosya</h3>
        <dl className="mt-3 space-y-2 text-sm text-[#475569]">
          <div className="flex justify-between gap-2">
            <dt>Ad</dt>
            <dd className="max-w-[62%] truncate text-right font-medium text-[#0f172a]">{selected.originalFilename}</dd>
          </div>
          <div className="flex justify-between gap-2">
            <dt>Dosya Kimliği</dt>
            <dd className="max-w-[62%] truncate text-right font-medium text-[#0f172a]">{selected.fileId}</dd>
          </div>
          <div className="flex justify-between gap-2">
            <dt>Proje</dt>
            <dd className="max-w-[62%] truncate text-right font-medium text-[#0f172a]">{selected.projectName}</dd>
          </div>
          <div className="flex justify-between gap-2">
            <dt>Yükleme Tarihi</dt>
            <dd className="font-medium text-[#0f172a]">{formatWorkspaceDate(selected.uploadedAt)}</dd>
          </div>
        </dl>
        <div className="mt-4 grid grid-cols-3 gap-2">
          <Link
            href={`/view/${selected.fileId}`}
            className="inline-flex h-9 items-center justify-center rounded-lg border border-[#d1dae6] bg-white text-xs font-medium text-[#1f2937]"
          >
            Görüntüle
          </Link>
          <Link
            href={`/projects/${selected.projectId}`}
            className="inline-flex h-9 items-center justify-center rounded-lg border border-[#d1dae6] bg-white text-xs font-medium text-[#1f2937]"
          >
            Proje
          </Link>
          <Link
            href={`${targetPath}?file=${encodeURIComponent(selected.fileId)}&project=${encodeURIComponent(selected.projectId)}`}
            className="inline-flex h-9 items-center justify-center rounded-lg border border-[#d1dae6] bg-white text-xs font-medium text-[#1f2937]"
          >
            Odakla
          </Link>
        </div>
      </div>
    </aside>
  );
}

function Inline3DViewport({
  fileId,
  interactionMode,
  clipEnabled,
  explodeEnabled,
  fitRequestKey,
  zoomRequest,
}: {
  fileId: string;
  interactionMode: ViewerInteractionMode;
  clipEnabled: boolean;
  explodeEnabled: boolean;
  fitRequestKey: number;
  zoomRequest: { key: number; direction: "in" | "out" };
}) {
  const [blobUrl, setBlobUrl] = useState<string | null>(null);
  const [renderMode, setRenderMode] = useState<RenderMode>("shadedEdges");
  const [cameraPreset, setCameraPreset] = useState<"iso" | "front" | "top" | "right">("iso");
  const [status, setStatus] = useState<"loading" | "ready" | "error">("loading");
  const [message, setMessage] = useState("Model hazırlanıyor...");
  const sourceUrlRef = useRef<string | null>(null);
  const objectUrlRef = useRef<string | null>(null);

  useEffect(() => {
    let cancelled = false;

    const load = async () => {
      try {
        const file = await getFile(fileId);
        if (cancelled) return;

        const state = (file.status || "").toLowerCase();
        if (state === "failed") {
          setStatus("error");
          setMessage(file.error || "Model dönüştürülemedi.");
          return;
        }

        if (state !== "ready" && state !== "succeeded") {
          setStatus("loading");
          setMessage("Model hazırlanıyor...");
          return;
        }

        const targetUrl =
          file.gltf_url ||
          file.lods?.lod2?.url ||
          file.lods?.lod1?.url ||
          file.lods?.lod0?.url ||
          null;
        if (!targetUrl) {
          setStatus("loading");
          setMessage("3D içerik henüz hazır değil.");
          return;
        }

        if (sourceUrlRef.current === targetUrl && objectUrlRef.current) {
          setBlobUrl(objectUrlRef.current);
          setStatus("ready");
          return;
        }

        const authedBlobUrl = await fetchAuthedBlobUrl(targetUrl);
        if (cancelled) {
          URL.revokeObjectURL(authedBlobUrl);
          return;
        }

        if (objectUrlRef.current) {
          URL.revokeObjectURL(objectUrlRef.current);
        }

        objectUrlRef.current = authedBlobUrl;
        sourceUrlRef.current = targetUrl;
        setBlobUrl(authedBlobUrl);
        setStatus("ready");
      } catch (error: unknown) {
        if (cancelled) return;
        setStatus("error");
        setMessage(error instanceof Error ? error.message : "Model yüklenemedi.");
      }
    };

    void load();
    const timer = window.setInterval(() => {
      void load();
    }, 3000);

    return () => {
      cancelled = true;
      window.clearInterval(timer);
      if (objectUrlRef.current) {
        URL.revokeObjectURL(objectUrlRef.current);
        objectUrlRef.current = null;
      }
      sourceUrlRef.current = null;
    };
  }, [fileId]);

  useEffect(() => {
    setCameraPreset("iso");
  }, [fitRequestKey, fileId]);

  return (
    <div className="relative h-full w-full bg-white">
      {status === "ready" && blobUrl ? (
        <>
          <ThreeViewer
            url={blobUrl}
            renderMode={renderMode}
            interactionMode={interactionMode}
            clip={clipEnabled}
            explode={explodeEnabled}
            cameraPreset={cameraPreset}
            onCameraPresetChange={setCameraPreset}
            fitRequestKey={fitRequestKey}
            zoomRequest={zoomRequest}
          />
          <div className="absolute left-3 top-3 rounded-lg border border-[#d1dae6] bg-white/95 p-2">
            <select
              value={renderMode}
              onChange={(event) => setRenderMode(event.target.value as RenderMode)}
              className="h-8 rounded-md border border-[#d1dae6] bg-white px-2 text-xs text-[#1f2937]"
            >
              <option value="shadedEdges">Shaded + Kenar</option>
              <option value="shaded">Shaded</option>
              <option value="wireframe">Wireframe</option>
              <option value="xray">X-Ray</option>
              <option value="pbr">PBR</option>
            </select>
          </div>
        </>
      ) : (
        <div className="grid h-full place-items-center bg-white p-6 text-sm text-[#64748b]">
          {status === "error" ? message : message}
        </div>
      )}
    </div>
  );
}

function Inline2DViewport({ fileId }: { fileId: string }) {
  const [blobUrl, setBlobUrl] = useState<string | null>(null);
  const [kind, setKind] = useState<"dxf" | "pdf" | "image" | "unknown">("unknown");
  const [status, setStatus] = useState<"loading" | "ready" | "error">("loading");
  const [message, setMessage] = useState("2D içerik hazırlanıyor...");
  const sourceUrlRef = useRef<string | null>(null);
  const objectUrlRef = useRef<string | null>(null);

  useEffect(() => {
    let cancelled = false;

    const load = async () => {
      try {
        const file = await getFile(fileId);
        if (cancelled) return;

        const state = (file.status || "").toLowerCase();
        if (state === "failed") {
          setStatus("error");
          setMessage(file.error || "2D içerik dönüştürülemedi.");
          return;
        }

        const lower = (file.original_filename || "").toLowerCase();
        if (lower.endsWith(".dxf")) {
          if (state !== "ready" && state !== "succeeded") {
            setStatus("loading");
            setMessage("2D çizim hazırlanıyor...");
            return;
          }
          setKind("dxf");
          setStatus("ready");
          return;
        }

        if (state !== "ready" && state !== "succeeded") {
          setStatus("loading");
          setMessage("2D içerik hazırlanıyor...");
          return;
        }

        const targetUrl = file.original_url || file.preview_url || null;
        if (!targetUrl) {
          setStatus("loading");
          setMessage("2D içerik henüz hazır değil.");
          return;
        }

        if (sourceUrlRef.current === targetUrl && objectUrlRef.current) {
          setBlobUrl(objectUrlRef.current);
          setStatus("ready");
          return;
        }

        const authedBlobUrl = await fetchAuthedBlobUrl(targetUrl);
        if (cancelled) {
          URL.revokeObjectURL(authedBlobUrl);
          return;
        }

        if (objectUrlRef.current) {
          URL.revokeObjectURL(objectUrlRef.current);
        }

        const contentType = (file.content_type || "").toLowerCase();
        const resolvedKind: "pdf" | "image" | "unknown" =
          contentType.includes("pdf") || lower.endsWith(".pdf")
            ? "pdf"
            : contentType.startsWith("image/") || /\.(png|jpg|jpeg|webp|bmp|gif|svg)$/i.test(lower)
            ? "image"
            : "unknown";

        objectUrlRef.current = authedBlobUrl;
        sourceUrlRef.current = targetUrl;
        setKind(resolvedKind);
        setBlobUrl(authedBlobUrl);
        setStatus("ready");
      } catch (error: unknown) {
        if (cancelled) return;
        setStatus("error");
        setMessage(error instanceof Error ? error.message : "2D içerik yüklenemedi.");
      }
    };

    void load();
    const timer = window.setInterval(() => {
      void load();
    }, 3000);

    return () => {
      cancelled = true;
      window.clearInterval(timer);
      if (objectUrlRef.current) {
        URL.revokeObjectURL(objectUrlRef.current);
        objectUrlRef.current = null;
      }
      sourceUrlRef.current = null;
    };
  }, [fileId]);

  if (status === "error") {
    return <div className="grid h-full place-items-center bg-white p-6 text-sm text-red-600">{message}</div>;
  }

  if (status !== "ready") {
    return <div className="grid h-full place-items-center bg-white p-6 text-sm text-[#64748b]">{message}</div>;
  }

  if (kind === "dxf") {
    return (
      <div className="h-full bg-white p-2">
        <DxfViewer fileId={fileId} />
      </div>
    );
  }

  if (!blobUrl) {
    return <div className="grid h-full place-items-center bg-white p-6 text-sm text-[#64748b]">2D içerik hazırlanıyor...</div>;
  }

  if (kind === "pdf") {
    return <iframe title="2D PDF" src={blobUrl} className="h-full w-full border-0 bg-white" />;
  }

  return (
    <div className="grid h-full place-items-center bg-white p-2">
      <img src={blobUrl} alt="2D Önizleme" className="max-h-full w-auto object-contain" />
    </div>
  );
}

export function HomeSurface() {
  const router = useRouter();
  const inputRef = useRef<HTMLInputElement>(null);
  const [dragging, setDragging] = useState(false);
  const [pickedFileName, setPickedFileName] = useState("");
  const [busy, setBusy] = useState(false);
  const [status, setStatus] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const onFilePick = useCallback(
    async (file: File | null | undefined) => {
      if (!file) return;
      setPickedFileName(file.name);
      setBusy(true);
      setStatus("Dosya yükleniyor...");
      setError(null);

      try {
        const result = await uploadDirect(file);
        const mode = detectWorkspaceMode(file.name, file.type || null);
        const saved = registerUploadedFile({
          fileId: result.file_id,
          originalFilename: file.name,
          sizeBytes: file.size,
          contentType: file.type || null,
          mode,
          projectId: DEFAULT_PROJECT_ID,
          projectName: DEFAULT_PROJECT_NAME,
        });
        setStatus("Yükleme tamamlandı. Dosya projeye eklendi.");

        const params = new URLSearchParams({
          file: saved.fileId,
          project: saved.projectId,
        });
        router.push(`${mode === "2d" ? "/app/2d" : "/app/3d"}?${params.toString()}`);
      } catch (err: unknown) {
        setError(err instanceof Error ? err.message : "Yükleme başarısız.");
      } finally {
        setBusy(false);
      }
    },
    [router]
  );

  return (
    <div className="space-y-6">
      <section className="rounded-2xl border border-[#d9e2ec] bg-white p-3 shadow-[0_2px_6px_rgba(15,23,42,0.05)]">
        <div
          className={[
            "relative h-[360px] overflow-hidden rounded-xl border border-[#dde3ec] bg-[#fbfcfe] transition",
            dragging ? "ring-2 ring-[#60a5fa]" : "",
          ].join(" ")}
          role="button"
          tabIndex={0}
          onClick={() => {
            if (!busy) inputRef.current?.click();
          }}
          onKeyDown={(event) => {
            if ((event.key === "Enter" || event.key === " ") && !busy) {
              event.preventDefault();
              inputRef.current?.click();
            }
          }}
          onDragOver={(event) => {
            event.preventDefault();
            setDragging(true);
          }}
          onDragLeave={(event) => {
            if (event.currentTarget.contains(event.relatedTarget as Node)) return;
            setDragging(false);
          }}
          onDrop={(event) => {
            event.preventDefault();
            setDragging(false);
            void onFilePick(event.dataTransfer.files?.[0] ?? null);
          }}
        >
          <div
            className="absolute inset-0"
            style={{
              backgroundImage:
                "repeating-linear-gradient(0deg, rgba(148,163,184,0.2) 0, rgba(148,163,184,0.2) 1px, transparent 1px, transparent 28px), repeating-linear-gradient(90deg, rgba(148,163,184,0.2) 0, rgba(148,163,184,0.2) 1px, transparent 1px, transparent 28px)",
            }}
          />

          <input
            ref={inputRef}
            type="file"
            className="hidden"
            disabled={busy}
            onChange={(event) => {
              void onFilePick(event.target.files?.[0] ?? null);
            }}
          />

          <div className="relative z-10 flex h-full flex-col justify-between p-6">
            <div className="max-w-2xl">
              <h1 className="text-[42px] font-semibold tracking-[-0.03em] text-[#0f172a]">STELLCODEX</h1>
              <p className="mt-2 text-3xl font-semibold text-[#0f172a]">2D ve 3D mühendislik görüntüleyicisi</p>
              <p className="mt-3 text-xl text-[#3b536d]">Dosyanızı sürükleyin veya alana tıklayarak yüklemeye başlayın.</p>
            </div>

            <div className="flex items-end justify-between gap-3">
              <button
                type="button"
                disabled={busy}
                onClick={(event) => {
                  event.stopPropagation();
                  inputRef.current?.click();
                }}
                className="inline-flex h-10 items-center rounded-xl border border-[#cbd5e1] bg-white px-4 text-sm font-medium text-[#1e293b] hover:bg-[#f8fafc] disabled:cursor-not-allowed disabled:opacity-60"
              >
                {busy ? "Yükleniyor..." : "Dosya Yükle"}
              </button>
              {pickedFileName ? (
                <p className="max-w-[60%] truncate text-sm text-[#334155]">Seçilen dosya: {pickedFileName}</p>
              ) : (
                <p className="text-sm text-[#64748b]">Sürükle-bırak desteklenir</p>
              )}
            </div>
          </div>
        </div>
      </section>

      {status ? (
        <div className="rounded-xl border border-[#dbe7fb] bg-[#f3f8ff] px-4 py-3 text-sm text-[#1e3a8a]">{status}</div>
      ) : null}
      {error ? <div className="rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">{error}</div> : null}

      <section>
        <h2 className="mb-3 text-[34px] font-semibold tracking-[-0.02em] text-[#0f172a]">Modlar</h2>
        <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-5">
          {modeCards.map((card) => (
            <Link
              key={card.title}
              href={card.href}
              className="rounded-2xl border border-[#dce3ee] bg-white p-4 shadow-[0_2px_6px_rgba(15,23,42,0.05)] transition hover:-translate-y-0.5 hover:shadow-[0_8px_16px_rgba(15,23,42,0.1)]"
            >
              <span className="inline-flex h-8 w-8 items-center justify-center rounded-lg border border-[#dce3ee] bg-[#f8fafc] text-xs font-semibold text-[#334155]">
                {card.icon}
              </span>
              <h3 className="mt-3 text-lg font-semibold text-[#0f172a]">{card.title}</h3>
              <p className="mt-1 text-sm text-[#58677a]">{card.desc}</p>
            </Link>
          ))}
        </div>
      </section>

      <section>
        <h2 className="mb-3 text-[34px] font-semibold tracking-[-0.02em] text-[#0f172a]">Son Dosyalarım</h2>
        <div className="rounded-2xl border border-[#dce3ee] bg-white p-5 shadow-[0_2px_6px_rgba(15,23,42,0.05)]">
          <h3 className="text-2xl font-semibold text-[#0f172a]">Henüz dosya yok</h3>
          <p className="mt-2 text-base text-[#58677a]">Henüz dosya yok. Dosya yükleyerek başlayın.</p>
          <div className="mt-4">
            <Link
              href="/dashboard"
              className="inline-flex h-10 items-center rounded-xl border border-[#cbd5e1] bg-white px-4 text-sm font-medium text-[#1e293b] hover:bg-[#f8fafc]"
            >
              Panele Git
            </Link>
          </div>
        </div>
      </section>
    </div>
  );
}

export function ViewerModuleSurface({
  title,
  variant = "3d",
  fileId,
  fileName,
}: {
  title: string;
  variant?: ViewerVariant;
  fileId?: string;
  fileName?: string;
}) {
  const viewerMinHeight = useViewerMinHeight();
  const tools = viewerToolsByVariant(variant);
  const selected = useResolvedWorkspaceFile(variant, fileId, fileName);
  const [activeTool, setActiveTool] = useState<string>(variant === "explode" ? "Patlat" : tools[0] || "");
  const [treeQuery, setTreeQuery] = useState("");
  const [leftTab, setLeftTab] = useState<"assembly" | "display" | "section">("assembly");
  const [leftPaneMode, setLeftPaneMode] = useState<LeftPaneMode>("normal");
  const [interactionMode, setInteractionMode] = useState<ViewerInteractionMode>("rotate");
  const [clipEnabled, setClipEnabled] = useState(variant === "explode");
  const [explodeEnabled, setExplodeEnabled] = useState(variant === "explode");
  const [fitRequestKey, setFitRequestKey] = useState(0);
  const [zoomRequest, setZoomRequest] = useState<{ key: number; direction: "in" | "out" }>({
    key: 0,
    direction: "in",
  });
  const [hiddenRows, setHiddenRows] = useState<Set<string>>(new Set());

  const assemblyRows = useMemo(() => {
    const baseName = (selected?.originalFilename || "model")
      .replace(/\.[^/.]+$/, "")
      .replace(/[^a-zA-Z0-9_-]/g, "_")
      .toLowerCase();
    return Array.from({ length: 16 }, (_, index) => `${baseName}_${index + 1}`);
  }, [selected?.originalFilename]);

  const filteredRows = useMemo(() => {
    const query = treeQuery.trim().toLowerCase();
    return assemblyRows.filter((row) => {
      if (hiddenRows.has(row)) return false;
      if (!query) return true;
      return row.includes(query);
    });
  }, [assemblyRows, hiddenRows, treeQuery]);

  const toggleRowVisibility = useCallback((row: string) => {
    setHiddenRows((prev) => {
      const next = new Set(prev);
      if (next.has(row)) {
        next.delete(row);
      } else {
        next.add(row);
      }
      return next;
    });
  }, []);

  useEffect(() => {
    if (variant === "explode") {
      setExplodeEnabled(true);
      setActiveTool("Patlat");
      return;
    }
    setExplodeEnabled(false);
    setActiveTool(tools[0] || "");
  }, [variant, tools]);

  const triggerFit = useCallback(() => {
    setFitRequestKey((prev) => prev + 1);
  }, []);

  const triggerZoom = useCallback((direction: "in" | "out") => {
    setZoomRequest((prev) => ({ key: prev.key + 1, direction }));
  }, []);

  const handleToolAction = useCallback(
    (action: string) => {
      setActiveTool(action);

      if (action === "Döndür") {
        setInteractionMode("rotate");
        return;
      }
      if (action === "Kaydır") {
        setInteractionMode("pan");
        return;
      }
      if (action === "Yakınlaştır") {
        triggerZoom("in");
        return;
      }
      if (action === "Uzaklaştır") {
        triggerZoom("out");
        return;
      }
      if (action === "Sığdır" || action === "Odak" || action === "Sıfırla") {
        triggerFit();
        return;
      }
      if (action === "Kesit") {
        setClipEnabled((prev) => !prev);
        return;
      }
      if (action === "Patlat" || action === "Adım") {
        setExplodeEnabled(true);
        return;
      }
      if (action === "Topla") {
        setExplodeEnabled(false);
      }
    },
    [triggerFit, triggerZoom]
  );

  const isToolActive = useCallback(
    (action: string) => {
      if (action === "Döndür") return interactionMode === "rotate";
      if (action === "Kaydır") return interactionMode === "pan";
      if (action === "Kesit") return clipEnabled;
      if (action === "Patlat") return explodeEnabled;
      if (action === "Topla") return !explodeEnabled;
      return activeTool === action;
    },
    [activeTool, clipEnabled, explodeEnabled, interactionMode]
  );

  const gridTemplateColumns = useMemo(() => {
    if (leftPaneMode === "hidden") return "minmax(0,1fr)";
    if (leftPaneMode === "wide") return "320px minmax(0,1fr)";
    return "230px minmax(0,1fr)";
  }, [leftPaneMode]);

  return (
    <section className="rounded-2xl border border-[#dce3ee] bg-white p-3 shadow-[0_2px_8px_rgba(15,23,42,0.06)]">
      <div className="mb-3 flex flex-wrap items-center gap-2">
        {tools.map((action) => (
          <button
            key={action}
            type="button"
            onClick={() => handleToolAction(action)}
            className={[
              "inline-flex h-9 items-center rounded-lg border px-3 text-xs font-medium transition",
              isToolActive(action)
                ? "border-[#1d4ed8] bg-[#eaf2ff] text-[#1e40af]"
                : "border-[#d1dae6] bg-white text-[#334155] hover:bg-[#f8fafc]",
            ].join(" ")}
          >
            {action}
          </button>
        ))}

        <div className="ml-auto flex flex-wrap items-center gap-2">
          <button
            type="button"
            onClick={() => setLeftPaneMode((prev) => (prev === "hidden" ? "normal" : "hidden"))}
            className="inline-flex h-9 items-center rounded-lg border border-[#d1dae6] bg-white px-3 text-xs font-medium text-[#334155] hover:bg-[#f8fafc]"
          >
            {leftPaneMode === "hidden" ? "Panel Aç" : "Panel Gizle"}
          </button>
          <button
            type="button"
            onClick={() => setLeftPaneMode("normal")}
            className={[
              "inline-flex h-9 items-center rounded-lg border px-3 text-xs font-medium",
              leftPaneMode === "normal"
                ? "border-[#1d4ed8] bg-[#eaf2ff] text-[#1e40af]"
                : "border-[#d1dae6] bg-white text-[#334155] hover:bg-[#f8fafc]",
            ].join(" ")}
          >
            Normal
          </button>
          <button
            type="button"
            onClick={() => setLeftPaneMode("wide")}
            className={[
              "inline-flex h-9 items-center rounded-lg border px-3 text-xs font-medium",
              leftPaneMode === "wide"
                ? "border-[#1d4ed8] bg-[#eaf2ff] text-[#1e40af]"
                : "border-[#d1dae6] bg-white text-[#334155] hover:bg-[#f8fafc]",
            ].join(" ")}
          >
            Geniş
          </button>
          {selected ? (
            <Link
              href={`/view/${selected.fileId}`}
              className="inline-flex h-9 items-center rounded-lg border border-[#d1dae6] bg-white px-3 text-xs font-medium text-[#1f2937] hover:bg-[#f8fafc]"
            >
              Tam Görünüm
            </Link>
          ) : null}
        </div>
      </div>

      <div className="grid gap-3" style={{ gridTemplateColumns }}>
        {leftPaneMode !== "hidden" ? (
          <aside
            className="flex h-full flex-col rounded-xl border border-[#dce3ee] bg-white p-3"
            style={{ height: viewerMinHeight }}
          >
            <div className="grid grid-cols-3 gap-1">
              {[
                { key: "assembly", label: "Assembly" },
                { key: "display", label: "View" },
                { key: "section", label: "Section" },
              ].map((tab) => (
                <button
                  key={tab.key}
                  type="button"
                  onClick={() => setLeftTab(tab.key as "assembly" | "display" | "section")}
                  className={[
                    "h-8 rounded-md border text-xs font-medium",
                    leftTab === tab.key
                      ? "border-[#1d4ed8] bg-[#eaf2ff] text-[#1e40af]"
                      : "border-[#d1dae6] bg-white text-[#334155] hover:bg-[#f8fafc]",
                  ].join(" ")}
                >
                  {tab.label}
                </button>
              ))}
            </div>

            <input
              type="search"
              value={treeQuery}
              onChange={(event) => setTreeQuery(event.target.value)}
              placeholder="Ağaçta ara..."
              className="mt-3 h-10 w-full rounded-lg border border-[#d1dae6] bg-white px-3 text-sm text-[#1f2937] outline-none focus:border-[#7aa2e3]"
            />

            <div className="mt-3 min-h-0 flex-1 space-y-1 overflow-y-auto rounded-lg border border-[#e2e8f0] bg-white p-2">
              {filteredRows.length ? (
                filteredRows.map((row) => (
                  <div key={row} className="flex items-center justify-between gap-2 rounded-md border border-[#eef2f7] px-2 py-1.5 text-xs">
                    <span className="truncate text-[#334155]">{row}</span>
                    <button
                      type="button"
                      onClick={() => toggleRowVisibility(row)}
                      className="inline-flex h-6 items-center rounded-md border border-[#d1dae6] bg-white px-2 text-[11px] text-[#334155] hover:bg-[#f8fafc]"
                    >
                      Gizle
                    </button>
                  </div>
                ))
              ) : (
                <div className="rounded-md border border-dashed border-[#d1dae6] px-3 py-4 text-center text-xs text-[#64748b]">
                  Sonuç bulunamadı.
                </div>
              )}
            </div>
          </aside>
        ) : null}

        <div className="rounded-xl border border-[#dce3ee] bg-white p-2">
          <ViewerFrame minHeight={viewerMinHeight}>
            <div className="relative h-full w-full overflow-hidden rounded-lg border border-[#dde3ec] bg-white text-sm text-[#64748b]">
              {selected ? (
                variant === "2d" ? (
                  <Inline2DViewport key={selected.fileId} fileId={selected.fileId} />
                ) : (
                  <Inline3DViewport
                    key={selected.fileId}
                    fileId={selected.fileId}
                    interactionMode={interactionMode}
                    clipEnabled={clipEnabled}
                    explodeEnabled={explodeEnabled}
                    fitRequestKey={fitRequestKey}
                    zoomRequest={zoomRequest}
                  />
                )
              ) : variant === "2d" ? (
                <div className="mx-auto w-full max-w-[680px] space-y-3 p-6">
                  <div className="h-3 w-40 rounded bg-[#e2e8f0]" />
                  <div className="h-[2px] w-full bg-[#cbd5e1]" />
                  <div className="grid grid-cols-3 gap-3">
                    <div className="h-24 rounded-lg border border-[#d8e1ec] bg-white" />
                    <div className="h-24 rounded-lg border border-[#d8e1ec] bg-white" />
                    <div className="h-24 rounded-lg border border-[#d8e1ec] bg-white" />
                  </div>
                  <div className="text-center text-xs text-[#64748b]">{viewerLabelByVariant(variant)}</div>
                </div>
              ) : variant === "explode" ? (
                <div className="grid h-full place-items-center">
                  <div className="grid grid-cols-3 gap-4 p-6">
                    {Array.from({ length: 9 }).map((_, index) => (
                      <div key={index} className="h-14 w-14 rounded-lg border border-[#d8e1ec] bg-white" />
                    ))}
                  </div>
                </div>
              ) : (
                <div className="grid h-full place-items-center p-6">
                  <div className="text-sm text-[#64748b]">{viewerLabelByVariant(variant)}</div>
                </div>
              )}
            </div>
          </ViewerFrame>

          <p className="mt-2 text-xs text-[#64748b]">
            {selected ? `${selected.originalFilename} görüntüleniyor.` : `${title} için görüntüleyici iskeleti`}
          </p>
        </div>
      </div>
    </section>
  );
}

export function RenderSurface({ fileId, fileName }: { fileId?: string; fileName?: string }) {
  const viewerMinHeight = useViewerMinHeight();
  const selected = useResolvedWorkspaceFile("render", fileId, fileName);

  return (
    <div className="grid gap-4 xl:grid-cols-[1fr_320px]">
      <section className="rounded-2xl border border-[#dce3ee] bg-white p-4 shadow-[0_2px_8px_rgba(15,23,42,0.06)]">
        <div className="mb-3 flex items-center justify-between gap-2">
          <h3 className="text-base font-semibold text-[#0f172a]">Render Önizleme</h3>
          <select className="h-10 rounded-lg border border-[#d1dae6] bg-white px-3 text-sm text-[#1f2937]">
            <option>Yüksek Kalite</option>
            <option>Sunum</option>
            <option>Taslak</option>
          </select>
        </div>

        <ViewerFrame minHeight={viewerMinHeight}>
          <div className="relative h-full w-full overflow-hidden rounded-xl border border-dashed border-[#cfd8e3] bg-[#f8fafd] text-sm text-[#64748b]">
            {selected ? (
              <iframe
                title="Render kaynak görüntü"
                src={`/view/${selected.fileId}`}
                className="h-full min-h-[inherit] w-full border-0"
                loading="lazy"
              />
            ) : (
              <div className="grid h-full place-items-center p-6">Render önizleme alanı</div>
            )}
          </div>
        </ViewerFrame>
      </section>

      <aside className="space-y-4">
        <SelectedFileCard selected={selected} variant="render" />
        <div className="rounded-2xl border border-[#dce3ee] bg-white p-4 shadow-[0_2px_8px_rgba(15,23,42,0.06)]">
          <h3 className="text-base font-semibold text-[#0f172a]">Render İşlemi</h3>
          <p className="mt-2 text-sm text-[#475569]">Preset, çözünürlük ve kalite değerlerini seçerek işlemi başlatın.</p>
          <div className="mt-4 space-y-2">
            <div className="h-10 rounded-lg border border-[#dce3ee] bg-[#f8fafc]" />
            <div className="h-10 rounded-lg border border-[#dce3ee] bg-[#f8fafc]" />
          </div>
          <button
            type="button"
            className="mt-4 inline-flex h-10 w-full items-center justify-center rounded-xl border border-[#1d4ed8] bg-[#2563eb] px-4 text-sm font-semibold text-white hover:bg-[#1d4ed8]"
          >
            Render Başlat
          </button>
        </div>
      </aside>
    </div>
  );
}

export function MoldCodesSurface() {
  return (
    <div className="grid gap-4 xl:grid-cols-[320px_1fr_320px]">
      <section className="rounded-2xl border border-[#dce3ee] bg-white p-4 shadow-[0_2px_8px_rgba(15,23,42,0.06)]">
        <h3 className="text-base font-semibold text-[#0f172a]">Kategoriler</h3>
        <ul className="mt-3 space-y-2 text-sm text-[#334155]">
          {["Yolluk Bileşenleri", "İtici Elemanlar", "Kılavuz Burçlar", "Standart Plakalar", "Bağlantı Elemanları"].map((item) => (
            <li key={item} className="rounded-lg border border-[#dce3ee] px-3 py-2">
              {item}
            </li>
          ))}
        </ul>
      </section>

      <section className="rounded-2xl border border-[#dce3ee] bg-white p-4 shadow-[0_2px_8px_rgba(15,23,42,0.06)]">
        <div className="flex flex-wrap items-center gap-3">
          <h3 className="text-base font-semibold text-[#0f172a]">Sonuçlar</h3>
          <input
            type="search"
            placeholder="Eleman kodu ara..."
            className="ml-auto h-10 rounded-lg border border-[#d1dae6] bg-white px-3 text-sm text-[#1f2937] outline-none focus:border-[#7aa2e3]"
          />
        </div>

        <div className="mt-3 grid gap-2">
          {Array.from({ length: 10 }).map((_, index) => (
            <div key={index} className="flex items-center justify-between rounded-lg border border-[#dce3ee] px-3 py-2 text-sm text-[#334155]">
              <span>MC-{(index + 1).toString().padStart(4, "0")}</span>
              <span className="text-xs text-[#64748b]">Standart Eleman</span>
            </div>
          ))}
        </div>
      </section>

      <aside className="rounded-2xl border border-[#dce3ee] bg-white p-4 shadow-[0_2px_8px_rgba(15,23,42,0.06)]">
        <h3 className="text-base font-semibold text-[#0f172a]">Teknik Özet</h3>
        <div className="mt-3 space-y-3">
          {["Çap", "Uzunluk", "Malzeme", "Sertlik", "Tolerans"].map((field) => (
            <div key={field} className="rounded-lg border border-[#dce3ee] px-3 py-2 text-sm text-[#475569]">
              {field}
            </div>
          ))}
        </div>
      </aside>
    </div>
  );
}

export function LibrarySurface({
  source,
}: {
  source: "tum" | "paylasilanlar" | "sablonlar" | "indirilenler";
}) {
  const chips = ["Tümü", "3D Model", "2D Çizim", "Render", "Patlatma"];
  const badgeMap: Record<typeof source, string> = {
    tum: "Kütüphane Akışı",
    paylasilanlar: "Paylaşılanlar",
    sablonlar: "Şablonlar",
    indirilenler: "İndirilenler",
  };

  return (
    <div className="space-y-4">
      <section className="rounded-2xl border border-[#dce3ee] bg-white p-4 shadow-[0_2px_8px_rgba(15,23,42,0.06)]">
        <div className="mb-4 flex flex-wrap gap-2">
          {chips.map((chip, index) => (
            <button
              key={chip}
              type="button"
              className={[
                "h-9 rounded-lg border px-3 text-sm",
                index === 0 ? "border-[#1d4ed8] bg-[#ebf3ff] text-[#124796]" : "border-[#d1dae6] bg-white text-[#334155]",
              ].join(" ")}
            >
              {chip}
            </button>
          ))}

          <span className="ml-auto inline-flex h-9 items-center rounded-lg border border-[#dce3ee] bg-[#f8fafc] px-3 text-xs font-semibold text-[#334155]">
            {badgeMap[source]}
          </span>
        </div>

        <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
          {Array.from({ length: 12 }).map((_, index) => (
            <article key={index} className="rounded-xl border border-[#dce3ee] bg-white p-3 shadow-[0_1px_2px_rgba(15,23,42,0.05)]">
              <div className="h-24 rounded-lg border border-dashed border-[#cad5e2] bg-[#f8fafd]" />
              <h3 className="mt-3 text-sm font-semibold text-[#0f172a]">Dosya-{index + 1}.step</h3>
              <p className="mt-1 text-xs text-[#64748b]">STEP · kullanıcı · 11.02.2026</p>
              <div className="mt-2 flex items-center gap-3 text-xs text-[#64748b]">
                <span>Beğeni</span>
                <span>Görüntüleme</span>
                <span>Yorum</span>
              </div>
            </article>
          ))}
        </div>
      </section>
    </div>
  );
}
