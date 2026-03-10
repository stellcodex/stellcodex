"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { useParams } from "next/navigation";
import { PrimaryButton } from "@/components/ui/PrimaryButton";
import { SecondaryButton } from "@/components/ui/SecondaryButton";
import { Card } from "@/components/ui/Card";
import { Container } from "@/components/ui/Container";
import { StatusPill } from "@/components/ui/StatusPill";
import { EmptyState } from "@/components/ui/EmptyState";
import { tokens } from "@/lib/tokens";
import { SCX_ID_REGEX } from "@/data/system-constants";
import { DxfViewer } from "@/components/viewer/DxfViewer";
import { ThreeViewer, RenderMode, ProjectionMode, ViewerNode, ViewerPartGroup } from "@/components/viewer/ThreeViewer";
import { CAMERA_PRESETS, QUALITY_DEFAULT, QUALITY_TO_LOD, QualityLevel, VIEWER_MODE_LABEL, VIEWER_MODE_ORDER } from "@/components/viewer/viewer-quality-config";
import {
  ApiHttpError,
  createShare,
  downloadScx,
  fetchAuthedBlobUrl,
  getFile,
  getFileManifest,
  getFileStatus,
  AssemblyTreeNode,
  FileDetail,
  FileManifest,
} from "@/services/api";

const STATUS_POLL_MS = 1500;
const VIEWER_WAIT_TIMEOUT_MS = 60_000;

type StatusInfo = {
  state: string;
  progress_hint?: string | null;
  progress_percent?: number | null;
  stage?: string | null;
};

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

type AssemblyRow = {
  key: string;
  occurrenceId: string;
  label: string;
  depth: number;
  nodeIds: string[];
};

type ViewerLookup = {
  byId: Set<string>;
  byName: Map<string, string[]>;
};

function readAssemblyChildren(node: AssemblyTreeNode): AssemblyTreeNode[] {
  return Array.isArray(node.children) ? node.children : [];
}

function readAssemblyLabel(node: AssemblyTreeNode, fallback: string): string {
  const labelCandidates = [node.display_name, node.name, node.label, node.id];
  for (const candidate of labelCandidates) {
    if (typeof candidate === "string" && candidate.trim().length > 0) return candidate;
  }
  return fallback;
}

function readOccurrenceId(node: AssemblyTreeNode): string | null {
  const candidates = [node.occurrence_id, node.id];
  for (const candidate of candidates) {
    if (typeof candidate === "string" && candidate.trim().length > 0) return candidate.trim();
  }
  return null;
}

function normalizeAssemblyTree(value: unknown): AssemblyTreeNode[] {
  if (!Array.isArray(value)) return [];
  const normalized: AssemblyTreeNode[] = [];
  value.forEach((node) => {
    if (!node || typeof node !== "object") return;
    const typed = node as AssemblyTreeNode;
    normalized.push({
      ...typed,
      children: normalizeAssemblyTree(typed.children),
    });
  });
  return normalized;
}

function filterAssemblyTree(nodes: AssemblyTreeNode[], queryLower: string): AssemblyTreeNode[] {
  if (!queryLower) return nodes;
  const filtered: AssemblyTreeNode[] = [];
  nodes.forEach((node, index) => {
    const label = readAssemblyLabel(node, `Item ${index + 1}`);
    const children = readAssemblyChildren(node);
    const filteredChildren = filterAssemblyTree(children, queryLower);
    if (label.toLowerCase().includes(queryLower) || filteredChildren.length > 0) {
      filtered.push({
        ...node,
        children: filteredChildren,
      });
    }
  });
  return filtered;
}

function uniqueStrings(values: string[]): string[] {
  return Array.from(new Set(values.filter((value) => value.trim().length > 0)));
}

function buildViewerLookup(nodes: ViewerNode[]): ViewerLookup {
  const byName = new Map<string, string[]>();
  const byId = new Set<string>();
  nodes.forEach((node) => {
    byId.add(node.id);
    const nameKey = (node.name || "").trim().toLowerCase();
    if (!nameKey) return;
    const existing = byName.get(nameKey) || [];
    existing.push(node.id);
    byName.set(nameKey, uniqueStrings(existing));
  });
  return { byId, byName };
}

function resolveAssemblyNodeIds(node: AssemblyTreeNode, lookup: ViewerLookup, label: string): string[] {
  const refs: string[] = [];
  const list = node.gltf_nodes;
  if (Array.isArray(list)) {
    list.forEach((item) => {
      if (typeof item === "string") refs.push(item);
    });
  }
  [node.gltf_node, node.node_ref, node.mesh_ref, node.name, node.display_name, node.label, node.id, label].forEach((value) => {
    if (typeof value === "string") refs.push(value);
  });

  const mapped: string[] = [];
  refs.forEach((ref) => {
    const trimmed = ref.trim();
    if (!trimmed) return;
    if (lookup.byId.has(trimmed)) {
      mapped.push(trimmed);
      return;
    }
    const byName = lookup.byName.get(trimmed.toLowerCase());
    if (byName) mapped.push(...byName);
  });
  return uniqueStrings(mapped);
}

function flattenAssemblyTree(nodes: AssemblyTreeNode[], lookup: ViewerLookup, depth = 0, parentKey = "root"): AssemblyRow[] {
  const rows: AssemblyRow[] = [];
  nodes.forEach((node, index) => {
    const label = readAssemblyLabel(node, `Item ${index + 1}`);
    const occurrenceId = readOccurrenceId(node);
    const rawKey =
      occurrenceId ||
      (typeof node.name === "string" && node.name) ||
      (typeof node.display_name === "string" && node.display_name) ||
      (typeof node.label === "string" && node.label) ||
      `node-${index}`;
    const key = `${parentKey}.${rawKey}.${index}`;
    const children = readAssemblyChildren(node);
    const childRows = flattenAssemblyTree(children, lookup, depth + 1, key);
    const nodeIds = uniqueStrings([
      ...resolveAssemblyNodeIds(node, lookup, label),
      ...childRows.flatMap((row) => row.nodeIds),
    ]);
    rows.push({ key: occurrenceId || key, occurrenceId: occurrenceId || key, label, depth, nodeIds });
    rows.push(...childRows);
  });
  return rows;
}

type ViewerError = {
  title: string;
  description: string;
};

function classifyViewerError(error: unknown): ViewerError {
  if (error instanceof ApiHttpError) {
    if (error.status === 404) {
      return { title: "Not found", description: "The file could not be found." };
    }
    if (error.status === 401) {
      return { title: "Unauthorized", description: error.message || "The guest token could not be issued." };
    }
    if (error.status === 403) {
      return { title: "Access denied", description: error.message || "You do not have permission to access this file." };
    }
    return { title: "Request failed", description: error.message || "Unexpected error." };
  }
  if (error instanceof Error) {
    const text = error.message.toLowerCase();
    if (text.includes("network") || text.includes("timeout")) {
      return { title: "Connection error", description: "The server could not be reached. Check the network and API routing." };
    }
    return { title: "Request failed", description: error.message };
  }
  return { title: "Request failed", description: "Unexpected error." };
}

export default function ViewPage() {
  const params = useParams();
  const fileId = typeof params.scx_id === "string" ? params.scx_id : "";
  const [file, setFile] = useState<FileDetail | null>(null);
  const [error, setError] = useState<ViewerError | null>(null);
  const [processing, setProcessing] = useState(false);
  const [statusInfo, setStatusInfo] = useState<StatusInfo | null>(null);
  const [blobUrl, setBlobUrl] = useState<string | null>(null);
  const [contentType, setContentType] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [processingSince, setProcessingSince] = useState<number | null>(null);
  const [processingElapsedMs, setProcessingElapsedMs] = useState(0);
  const [retryTick, setRetryTick] = useState(0);
  const [renderMode, setRenderMode] = useState<RenderMode>("shadedEdges");
  const [projection, setProjection] = useState<ProjectionMode>("perspective");
  const [clip, setClip] = useState(false);
  const [clipOffset, setClipOffset] = useState(0);
  const [clipAxis, setClipAxis] = useState<"x" | "y" | "z" | "free">("y");
  const [explodeFactor, setExplodeFactor] = useState(0);
  const [manifest, setManifest] = useState<FileManifest | null>(null);
  const [assemblyTree, setAssemblyTree] = useState<AssemblyTreeNode[]>([]);
  const [partCount, setPartCount] = useState(0);
  const [selectedTreeKey, setSelectedTreeKey] = useState<string | null>(null);
  const [viewerNodes, setViewerNodes] = useState<ViewerNode[]>([]);
  const [hiddenNodeIds, setHiddenNodeIds] = useState<Set<string>>(new Set());
  const [isolatedTreeKey, setIsolatedTreeKey] = useState<string | null>(null);
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
  const [leftDrawerOpen, setLeftDrawerOpen] = useState(false);
  const [rightDrawerOpen, setRightDrawerOpen] = useState(false);
  const [panelCollapsed, setPanelCollapsed] = useState(false);
  const [panelTab, setPanelTab] = useState<"state" | "parts" | "share">("parts");
  const [fitRequestKey, setFitRequestKey] = useState(0);
  const [zoomTick, setZoomTick] = useState(0);
  const [zoomDirection, setZoomDirection] = useState<"in" | "out">("in");
  const screenshotRef = useRef<(() => string | null) | null>(null);
  const viewRef = useRef<HTMLDivElement | null>(null);
  const objectUrlRef = useRef<string | null>(null);
  const lastResolvedUrlRef = useRef<string | null>(null);

  const is2d = file ? is2dFile(file) : false;

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
      setError({ title: "Not found", description: "Invalid file identifier." });
      setLoading(false);
      setProcessing(false);
      setProcessingSince(null);
      setProcessingElapsedMs(0);
      setManifest(null);
      setAssemblyTree([]);
      setPartCount(0);
      setSelectedTreeKey(null);
      return;
    }
    setFile(null);
    setBlobUrl(null);
    setContentType(null);
    setStatusInfo(null);
    setError(null);
    setProcessingSince(null);
    setProcessingElapsedMs(0);
    setHiddenNodeIds(new Set());
    setIsolatedTreeKey(null);
    setViewerNodes([]);
    setManifest(null);
    setAssemblyTree([]);
    setPartCount(0);
    setSelectedTreeKey(null);
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
          setProcessingSince(null);
          setLoading(false);
          setError({ title: "Operation failed", description: "Conversion failed. Try again." });
          return;
        }
        if (status.state !== "succeeded" && status.state !== "ready") {
          setProcessing(true);
          setProcessingSince((prev) => prev ?? Date.now());
          setLoading(false);
          schedule();
          return;
        }

        const [f, manifestData] = await Promise.all([
          getFile(fileId),
          getFileManifest(fileId).catch(() => null),
        ]);
        if (cancelled) return;
        const nextAssemblyTree = normalizeAssemblyTree(manifestData?.assembly_tree);
        setManifest(manifestData);
        setAssemblyTree(nextAssemblyTree);
        setPartCount(typeof manifestData?.part_count === "number" && manifestData.part_count >= 0 ? manifestData.part_count : 0);
        setSelectedTreeKey(null);
        setTreeQuery("");
        setFile(f);
        if (f.quality_default && ["Ultra", "High", "Medium", "Low"].includes(f.quality_default)) {
          setQuality(f.quality_default as QualityLevel);
        }
        setLoading(false);
        setProcessing(false);
        setProcessingSince(null);
        setProcessingElapsedMs(0);
        if (is2dFile(f)) {
          setContentType(f.content_type);
          if (f.original_filename.toLowerCase().endsWith(".dxf")) {
            lastResolvedUrlRef.current = null;
            setBlobUrl(null);
            return;
          }
          if (!f.original_url) {
            setError({ title: "Content not ready", description: "2D content is not ready yet. Try again." });
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
          setError({ title: "Content not ready", description: "3D content is not ready yet. Try again." });
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
          setProcessing(false);
          setProcessingSince(null);
          setError(classifyViewerError(e));
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

  useEffect(() => {
    setLeftDrawerOpen(false);
    setRightDrawerOpen(false);
    setPanelCollapsed(false);
    setPanelTab("parts");
  }, [fileId]);

  useEffect(() => {
    if (!processing || !processingSince) return;
    const tick = () => setProcessingElapsedMs(Date.now() - processingSince);
    tick();
    const intervalId = window.setInterval(tick, 1000);
    return () => {
      window.clearInterval(intervalId);
    };
  }, [processing, processingSince]);

  const handleShare = async () => {
    if (!fileId) return;
    setShareBusy(true);
    setShareError(null);
    try {
      const res = await createShare(fileId);
      const link = `${window.location.origin}/s/${res.token}`;
      setShareLink(link);
    } catch (e: any) {
      setShareError((e?.message || "The share link could not be created") + ". Try again.");
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
      setError(classifyViewerError(e));
    }
  };

  const filteredAssemblyTree = useMemo(() => {
    const q = treeQuery.trim().toLowerCase();
    return filterAssemblyTree(assemblyTree, q);
  }, [assemblyTree, treeQuery]);

  const viewerLookup = useMemo(() => buildViewerLookup(viewerNodes), [viewerNodes]);
  const manifestRows = useMemo(
    () => flattenAssemblyTree(filteredAssemblyTree, viewerLookup),
    [filteredAssemblyTree, viewerLookup]
  );
  const meshViewerNodes = useMemo(
    () => viewerNodes.filter((node) => node.type.toLowerCase().includes("mesh")),
    [viewerNodes]
  );
  const assemblyRows = manifestRows;
  const mappedAssemblyRows = useMemo(
    () => assemblyRows.filter((row) => row.nodeIds.length > 0),
    [assemblyRows]
  );
  const selectedRow = useMemo(
    () => assemblyRows.find((row) => row.key === selectedTreeKey) || null,
    [assemblyRows, selectedTreeKey]
  );
  const selectedNodeIds = selectedRow?.nodeIds || [];
  const selectedNodeId = selectedNodeIds[0] || null;
  const allViewerNodeIds = useMemo(
    () => Array.from(new Set((meshViewerNodes.length > 0 ? meshViewerNodes : viewerNodes).map((node) => node.id))),
    [meshViewerNodes, viewerNodes]
  );
  const explodePartGroups = useMemo<ViewerPartGroup[]>(
    () => mappedAssemblyRows.map((row) => ({ partId: row.occurrenceId, nodeIds: row.nodeIds })),
    [mappedAssemblyRows]
  );
  const explodeAvailable = explodePartGroups.length > 0;
  const canActOnSelection = selectedNodeIds.length > 0 && allViewerNodeIds.length > 0;
  const effectivePartCount = partCount > 0 ? partCount : assemblyRows.length;
  const processingPercent = Math.max(
    1,
    Math.min(
      99,
      typeof statusInfo?.progress_percent === "number"
        ? statusInfo.progress_percent
        : statusInfo?.state === "queued"
        ? 10
        : statusInfo?.state === "succeeded"
        ? 100
        : 55
    )
  );
  const processingTimedOut = processingElapsedMs >= VIEWER_WAIT_TIMEOUT_MS;
  const zoomRequest = useMemo(
    () => ({ key: zoomTick, direction: zoomDirection }),
    [zoomTick, zoomDirection]
  );

  const handleHideShow = () => {
    if (!canActOnSelection) return;
    setHiddenNodeIds((prev) => {
      const next = new Set(prev);
      const shouldHide = selectedNodeIds.some((id) => !next.has(id));
      selectedNodeIds.forEach((id) => {
        if (shouldHide) next.add(id);
        else next.delete(id);
      });
      return next;
    });
    setIsolatedTreeKey(null);
  };

  const handleIsolate = () => {
    if (!canActOnSelection || !selectedRow) return;
    if (isolatedTreeKey === selectedRow.key) {
      setHiddenNodeIds(new Set());
      setIsolatedTreeKey(null);
      return;
    }
    const selectedSet = new Set(selectedNodeIds);
    setHiddenNodeIds(new Set(allViewerNodeIds.filter((id) => !selectedSet.has(id))));
    setIsolatedTreeKey(selectedRow.key);
  };

  useEffect(() => {
    if (!selectedTreeKey) return;
    if (!assemblyRows.some((row) => row.key === selectedTreeKey)) {
      setSelectedTreeKey(null);
    }
  }, [assemblyRows, selectedTreeKey]);

  useEffect(() => {
    if (!explodeAvailable && explodeFactor !== 0) {
      setExplodeFactor(0);
    }
  }, [explodeAvailable, explodeFactor]);

  const viewerBody = useMemo(() => {
    if (!fileId) {
      return (
        <EmptyState
          title="File not found"
          description="The file could not be found. Start a new upload."
          action={<SecondaryButton href="/">Go to workspace</SecondaryButton>}
        />
      );
    }
    if (error) {
      return (
        <EmptyState
          title={error.title}
          description={error.description}
          action={
            <div className="flex flex-wrap items-center gap-2">
              <SecondaryButton onClick={() => setRetryTick((t) => t + 1)}>Retry</SecondaryButton>
              <PrimaryButton href="/">Go to workspace</PrimaryButton>
            </div>
          }
        />
      );
    }
    if (is2d && file?.original_filename.toLowerCase().endsWith(".dxf")) {
      return (
        <div className="h-full overflow-hidden rounded-2xl border border-[#e5e7eb] bg-white p-4">
          <DxfViewer fileId={fileId} />
        </div>
      );
    }

    if (loading || processing || !blobUrl) {
      const statusRaw = (statusInfo?.state || "running").toLowerCase();
      const status = statusRaw === "failed" ? "failed" : statusRaw === "succeeded" ? "ready" : statusRaw === "queued" ? "queued" : "running";
      const statusLabel = statusInfo?.progress_hint
        ? `Processing... (${statusInfo.progress_hint})`
        : "Processing...";
      return (
        <Card className="p-5">
          <div className="mb-4 flex items-center gap-3">
            <StatusPill status={status} label={statusLabel} />
            <span style={tokens.typography.body} className="text-[#6b7280]">Preparing the viewer...</span>
          </div>
          <div className="mb-3 h-2 overflow-hidden rounded-full bg-[#e5e7eb]">
            <div className="h-full rounded-full bg-[#111827] transition-all" style={{ width: `${processingPercent}%` }} />
          </div>
          <div className="h-[60vh] w-full animate-pulse rounded-xl bg-[#e6e2d8]" />
          <div className="mt-4 grid gap-2 text-xs text-[#6b7280]">
            <span>
              Updating status... {(processingElapsedMs / 1000).toFixed(0)}s
              {statusInfo?.stage ? ` · stage: ${statusInfo.stage}` : ""}
            </span>
            <div className="flex flex-wrap items-center gap-2">
              <SecondaryButton href="/">Back to workspace</SecondaryButton>
              <SecondaryButton onClick={() => setRetryTick((t) => t + 1)}>Retry</SecondaryButton>
            </div>
            {processingTimedOut ? (
              <div className="rounded-lg border border-amber-300 bg-amber-50 px-3 py-2 text-amber-700">
                Preparation is taking longer than expected. You can retry without discarding the background job.
              </div>
            ) : null}
          </div>
        </Card>
      );
    }

    if (is2d) {
      return (
        <div className="h-full overflow-hidden rounded-2xl border border-[#e5e7eb] bg-white p-4">
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
      <Card className="h-full overflow-hidden">
        <div ref={viewRef} className="h-full">
          <ThreeViewer
            url={blobUrl}
            renderMode={renderMode}
            projection={projection}
            cameraPreset={cameraPreset}
            fitRequestKey={fitRequestKey}
            zoomRequest={zoomRequest}
            clip={clip}
            clipOffset={clipOffset}
            clipAxis={clipAxis}
            explode={explodeAvailable && explodeFactor > 0}
            explodeFactor={explodeAvailable ? explodeFactor : 0}
            explodeGroups={explodePartGroups}
            hiddenNodes={hiddenNodeIds}
            selectedId={selectedNodeId}
            measureEnabled={measureEnabled}
            onMeasure={handleMeasure}
            onScreenshotReady={handleScreenshotReady}
            onNodes={setViewerNodes}
            onSelect={(node) => {
              if (!node) return;
              const matching = mappedAssemblyRows.find((row) => row.nodeIds.includes(node.id));
              if (matching) setSelectedTreeKey(matching.key);
            }}
          />
        </div>
      </Card>
    );
  }, [
    fileId,
    error,
    loading,
    processing,
    blobUrl,
    is2d,
    file,
    statusInfo,
    processingPercent,
    processingTimedOut,
    processingElapsedMs,
    contentType,
    pdfPage,
    renderMode,
    projection,
    fitRequestKey,
    zoomRequest,
    clip,
    clipOffset,
    clipAxis,
    explodeFactor,
    explodeAvailable,
    explodePartGroups,
    hiddenNodeIds,
    selectedNodeId,
    measureEnabled,
    handleMeasure,
    handleScreenshotReady,
    mappedAssemblyRows,
  ]);

  const panelContent = (
    <div className="flex h-full flex-col gap-3 p-3">
      <div className="grid grid-cols-3 gap-1 rounded-lg border border-[#d1d5db] bg-[#f8fafc] p-1 text-[11px]">
        <button className={`rounded px-2 py-1 ${panelTab === "state" ? "bg-white font-semibold text-[#111827]" : "text-[#4b5563]"}`} onClick={() => setPanelTab("state")}>State</button>
        <button className={`rounded px-2 py-1 ${panelTab === "parts" ? "bg-white font-semibold text-[#111827]" : "text-[#4b5563]"}`} onClick={() => setPanelTab("parts")}>Parts</button>
        <button className={`rounded px-2 py-1 ${panelTab === "share" ? "bg-white font-semibold text-[#111827]" : "text-[#4b5563]"}`} onClick={() => setPanelTab("share")}>Share</button>
      </div>

      {panelTab === "state" ? (
        <div className="grid gap-3 text-xs text-[#374151]">
          <div className="rounded-lg border border-[#e5e7eb] bg-[#f9fafb] px-2 py-2">
            Parts: <span className="font-semibold text-[#111827]">{effectivePartCount}</span>
            <span className="mx-2 text-[#9ca3af]">|</span>
            Hidden: <span className="font-semibold text-[#111827]">{hiddenNodeIds.size}</span>
          </div>
          <div className="grid gap-2">
            <div className="font-semibold text-[#111827]">Render Mode</div>
            <div className="grid grid-cols-2 gap-2">
              {VIEWER_MODE_ORDER.map((mode) => (
                <button
                  key={mode}
                  type="button"
                  className={`rounded border px-2 py-1 ${renderMode === mode ? "border-[#111827] bg-[#111827] text-white" : "border-[#d1d5db] bg-white"}`}
                  onClick={() => setRenderMode(mode)}
                >
                  {VIEWER_MODE_LABEL[mode]}
                </button>
              ))}
            </div>
          </div>
          <div className="grid gap-2">
            <div className="font-semibold text-[#111827]">Projection</div>
            <div className="grid grid-cols-2 gap-2">
              {(["perspective", "orthographic"] as ProjectionMode[]).map((mode) => (
                <button
                  key={mode}
                  type="button"
                  className={`rounded border px-2 py-1 ${projection === mode ? "border-[#111827] bg-[#111827] text-white" : "border-[#d1d5db] bg-white"}`}
                  onClick={() => setProjection(mode)}
                >
                  {mode === "perspective" ? "Perspective" : "Orthographic"}
                </button>
              ))}
            </div>
          </div>
          {!is2d ? (
            <div className="grid gap-2">
              <div className="font-semibold text-[#111827]">Explode</div>
              {!explodeAvailable ? (
                <div className="rounded border border-[#e5e7eb] bg-[#f9fafb] px-2 py-2 text-[11px] text-[#6b7280]">
                  Explode is disabled because assembly_meta mapping is missing.
                </div>
              ) : null}
              <label className="grid gap-1">
                <span>Factor ({explodeFactor.toFixed(2)})</span>
                <input
                  type="range"
                  min={0}
                  max={1}
                  step={0.01}
                  value={explodeFactor}
                  disabled={!explodeAvailable}
                  onChange={(e) => setExplodeFactor(Number(e.target.value))}
                />
              </label>
              <button
                type="button"
                className="rounded border border-[#d1d5db] bg-white px-2 py-1"
                disabled={!explodeAvailable}
                onClick={() => setExplodeFactor(0)}
              >
                Reset Explode
              </button>
            </div>
          ) : null}
          <div className="grid gap-2">
            <div className="font-semibold text-[#111827]">Section</div>
            <div className="grid grid-cols-4 gap-1">
              {(["x", "y", "z", "free"] as const).map((axis) => (
                <button
                  key={axis}
                  type="button"
                  onClick={() => setClipAxis(axis)}
                  className={`rounded border px-2 py-1 ${clipAxis === axis ? "border-[#111827] bg-[#111827] text-white" : "border-[#d1d5db] bg-white"}`}
                >
                  {axis.toUpperCase()}
                </button>
              ))}
            </div>
            <label className="flex items-center justify-between">
              Clip
              <input type="checkbox" checked={clip} onChange={(e) => setClip(e.target.checked)} />
            </label>
            <input type="range" min={-2} max={2} step={0.01} value={clipOffset} onChange={(e) => setClipOffset(Number(e.target.value))} />
          </div>
        </div>
      ) : null}

      {panelTab === "parts" ? (
        <div className="grid min-h-0 flex-1 gap-2">
          <input
            value={treeQuery}
            onChange={(e) => setTreeQuery(e.target.value)}
            placeholder="Search parts..."
            disabled={assemblyRows.length === 0}
            className="h-9 rounded-lg border border-[#d1d5db] bg-white px-2 text-xs"
          />
          <div className="rounded-lg border border-[#e5e7eb] bg-[#f9fafb] px-2 py-2 text-[11px] text-[#6b7280]">
            Select a part in the tree, then use the top toolbar for isolate and visibility actions.
          </div>
          <div className="min-h-0 overflow-auto rounded-lg border border-[#e5e7eb] bg-[#f9fafb] p-2 text-xs text-[#374151]">
            {assemblyRows.length === 0 ? (
              <div className="text-[#6b7280]">Assembly tree not available.</div>
            ) : (
              assemblyRows.map((row) => (
                <button
                  key={row.key}
                  type="button"
                  className={`mt-0.5 w-full truncate rounded px-2 py-1 text-left ${
                    selectedTreeKey === row.key ? "bg-[#e0e7ff] text-[#111827]" : "text-[#374151] hover:bg-[#eef2ff]"
                  } ${row.nodeIds.length === 0 ? "opacity-60" : ""}`}
                  style={{ paddingLeft: `${Math.min(row.depth * 12 + 8, 84)}px` }}
                  onClick={() => setSelectedTreeKey(row.key)}
                  title={row.nodeIds.length === 0 ? "No glTF mapping is available for this occurrence." : undefined}
                >
                  {row.label}
                </button>
              ))
            )}
          </div>
        </div>
      ) : null}

      {panelTab === "share" ? (
        <div className="grid gap-2 text-xs text-[#374151]">
          <div className="font-semibold text-[#111827]">Share Link</div>
          <PrimaryButton onClick={handleShare} disabled={shareBusy}>
            {shareBusy ? "Creating..." : "Create link"}
          </PrimaryButton>
          {shareLink ? (
            <div className="grid gap-2">
              <input readOnly value={shareLink} className="h-9 rounded-lg border border-[#d1d5db] bg-white px-2 text-xs" />
              <SecondaryButton onClick={handleCopy}>Copy</SecondaryButton>
            </div>
          ) : null}
          {shareError ? <div className="text-red-600">{shareError}</div> : null}
          <div className="rounded border border-[#e5e7eb] bg-[#f9fafb] px-2 py-2 text-[11px] text-[#6b7280]">
            Default permission: view-only.
          </div>
        </div>
      ) : null}
    </div>
  );

  return (
    <main className="h-full overflow-hidden">
      <div className="h-full px-2 sm:px-3">
        <div className="flex h-full flex-col gap-2 py-2 sm:py-3">
          <Card className="p-3">
            <div className="flex flex-wrap items-center justify-between gap-2">
              <div className="flex items-center gap-2">
                <SecondaryButton href="/">Back to workspace</SecondaryButton>
                <div style={tokens.typography.body} className="max-w-[40vw] truncate text-[#6b7280] sm:max-w-none">
                  {file ? shortName(file.original_filename) : "Viewer"}
                </div>
              </div>
              {/* Keep the top toolbar as the single action surface to avoid duplicated
                  controls across the viewer and side panels. */}
              <div className="flex flex-wrap items-center gap-2">
                {CAMERA_PRESETS.map((preset) => (
                  <button
                    key={preset.key}
                    type="button"
                    className={`rounded border px-2 py-1 text-xs ${
                      cameraPreset === preset.key ? "border-[#111827] bg-[#111827] text-white" : "border-[#d1d5db] bg-white text-[#374151]"
                    }`}
                    onClick={() => setCameraPreset(preset.key)}
                  >
                    {preset.label}
                  </button>
                ))}
                <button type="button" className="rounded border border-[#d1d5db] bg-white px-2 py-1 text-xs" onClick={() => setFitRequestKey((v) => v + 1)}>Fit</button>
                <button type="button" className="rounded border border-[#d1d5db] bg-white px-2 py-1 text-xs" onClick={handleIsolate} disabled={!canActOnSelection}>Isolate</button>
                <button type="button" className="rounded border border-[#d1d5db] bg-white px-2 py-1 text-xs" onClick={handleHideShow} disabled={!canActOnSelection}>Hide/Show</button>
                <button type="button" className="rounded border border-[#d1d5db] bg-white px-2 py-1 text-xs" onClick={() => setMeasureEnabled((v) => !v)}>
                  {measureEnabled ? "Measure Off" : "Measure"}
                </button>
                <button type="button" className="rounded border border-[#d1d5db] bg-white px-2 py-1 text-xs" onClick={handleScreenshot}>Export PNG</button>
                <button type="button" className="rounded border border-[#d1d5db] bg-white px-2 py-1 text-xs" onClick={handleDownloadScx}>Download</button>
                <button type="button" className="rounded border border-[#d1d5db] bg-white px-2 py-1 text-xs" onClick={toggleFullscreen}>Full</button>
                <button type="button" className="rounded border border-[#d1d5db] bg-white px-2 py-1 text-xs lg:hidden" onClick={() => setRightDrawerOpen(true)}>Panel</button>
                <button type="button" className="rounded border border-[#d1d5db] bg-white px-2 py-1 text-xs" onClick={() => setPanelCollapsed((v) => !v)}>
                  {panelCollapsed ? "Open panel" : "Close panel"}
                </button>
                <button type="button" className="rounded border border-[#d1d5db] bg-white px-2 py-1 text-xs" onClick={() => { setZoomDirection("in"); setZoomTick((v) => v + 1); }}>Zoom+</button>
                <button type="button" className="rounded border border-[#d1d5db] bg-white px-2 py-1 text-xs" onClick={() => { setZoomDirection("out"); setZoomTick((v) => v + 1); }}>Zoom-</button>
              </div>
            </div>
          </Card>

          <div className="flex min-h-0 flex-1 gap-3">
            <div className="min-w-0 flex-1">{viewerBody}</div>
            {!panelCollapsed ? (
              <aside className="hidden h-full w-[320px] shrink-0 overflow-hidden rounded-xl border border-[#d1d5db] bg-white lg:block">
                {panelContent}
              </aside>
            ) : null}
          </div>
        </div>
      </div>

      {rightDrawerOpen ? (
        <div className="fixed inset-0 z-50 lg:hidden">
          <button
            type="button"
            className="absolute inset-0 bg-black/35"
            onClick={() => setRightDrawerOpen(false)}
            aria-label="Close panel"
          />
          <aside className="absolute bottom-0 left-0 right-0 max-h-[82vh] overflow-y-auto rounded-t-2xl border border-[#d1d5db] bg-white">
            <div className="sticky top-0 flex items-center justify-between border-b border-[#e5e7eb] bg-white px-3 py-2 text-xs font-semibold text-[#374151]">
              <span>Viewer Panel</span>
              <button type="button" className="rounded border border-[#d1d5db] px-2 py-1" onClick={() => setRightDrawerOpen(false)}>
                Close
              </button>
            </div>
            {panelContent}
          </aside>
        </div>
      ) : null}
    </main>
  );
}

function PanZoomImage({ src }: { src: string }) {
  const [scale, setScale] = useState(1);
  const [offset, setOffset] = useState({ x: 0, y: 0 });
  const dragging = useRef(false);
  const lastPos = useRef({ x: 0, y: 0 });
  const hostRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    const host = hostRef.current;
    if (!host) return;
    const onWheel = (event: WheelEvent) => {
      event.preventDefault();
      const delta = event.deltaY < 0 ? 1.1 : 0.9;
      setScale((s) => Math.min(10, Math.max(0.2, s * delta)));
    };
    host.addEventListener("wheel", onWheel, { passive: false });
    return () => {
      host.removeEventListener("wheel", onWheel);
    };
  }, []);

  useEffect(() => {
    setScale(1);
    setOffset({ x: 0, y: 0 });
  }, [src]);

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
      ref={hostRef}
      className="relative h-full w-full overflow-hidden rounded-xl border border-[#e3dfd3] bg-white"
      style={{ touchAction: "none" }}
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
