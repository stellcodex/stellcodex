import type {
  RawAssemblyTreeNode,
  RawFileDetail,
  RawFileManifest,
  RawFileStatus,
  RawFileSummary,
} from "@/lib/contracts/files";
import type { FileRecord, StatusTone, ViewerModel, ViewerNodeRecord } from "@/lib/contracts/ui";

function mapStatusTone(status: string): StatusTone {
  const normalized = status.toLowerCase();
  if (normalized === "ready" || normalized === "approved") return "success";
  if (normalized === "failed") return "danger";
  if (normalized === "queued" || normalized === "processing" || normalized === "running") return "warning";
  if (normalized === "share ready") return "info";
  return "neutral";
}

export function mapFileRecord(input: RawFileSummary | RawFileDetail): FileRecord {
  return {
    fileId: input.file_id,
    originalName: input.original_name,
    kind: input.kind,
    mode: input.mode ?? null,
    createdAt: input.created_at,
    contentType: input.content_type,
    sizeBytes: input.size_bytes,
    status: input.status,
    statusTone: mapStatusTone(input.status),
    visibility: input.visibility,
    thumbnailUrl: input.thumbnail_url ?? null,
    previewUrl: input.preview_url ?? null,
    previewUrls: input.preview_urls ?? [],
    gltfUrl: input.gltf_url ?? null,
    originalUrl: input.original_url ?? null,
    partCount: input.part_count ?? null,
    error: input.error ?? null,
  };
}

export function mapViewerNode(node: RawAssemblyTreeNode): ViewerNodeRecord {
  const children = Array.isArray(node.children) ? node.children.map(mapViewerNode) : [];
  const occurrenceId = node.occurrence_id || node.id || "occurrence";
  return {
    id: node.id || occurrenceId,
    occurrenceId,
    partId: node.part_id || occurrenceId,
    label: node.display_name || node.name || occurrenceId,
    kind: node.kind || (children.length > 0 ? "assembly" : "part"),
    partCount: typeof node.part_count === "number" ? node.part_count : children.length > 0 ? 0 : 1,
    gltfNodes: Array.isArray(node.gltf_nodes) ? node.gltf_nodes.filter((item) => typeof item === "string") : [],
    children,
  };
}

export function countOccurrenceNodes(nodes: ViewerNodeRecord[]): number {
  return nodes.reduce((total, node) => {
    if (node.children.length === 0) return total + Math.max(node.partCount, 1);
    return total + countOccurrenceNodes(node.children);
  }, 0);
}

export function mapViewerModel(params: {
  file: RawFileDetail;
  status: RawFileStatus;
  manifest: RawFileManifest | null;
}): ViewerModel {
  const file = mapFileRecord(params.file);
  const nodes = (params.manifest?.assembly_tree ?? []).map(mapViewerNode);
  const occurrenceCount = countOccurrenceNodes(nodes);
  const is3d = file.kind === "3d";

  if (file.status.toLowerCase() === "failed" || params.status.state.toLowerCase() === "failed") {
    return {
      file,
      state: "failed",
      stateMessage: file.error || "Processing failed for this file.",
      modelId: params.manifest?.model_id ?? null,
      modelUrl: file.gltfUrl,
      contentUrl: file.originalUrl,
      previewUrls: file.previewUrls,
      nodes,
      occurrenceCount,
    };
  }

  if (file.status.toLowerCase() !== "ready" || params.status.state.toLowerCase() !== "succeeded") {
    return {
      file,
      state: "processing",
      stateMessage: params.status.progress_hint || "The file is still processing.",
      modelId: params.manifest?.model_id ?? null,
      modelUrl: file.gltfUrl,
      contentUrl: file.originalUrl,
      previewUrls: file.previewUrls,
      nodes,
      occurrenceCount,
    };
  }

  if (is3d && (nodes.length === 0 || occurrenceCount <= 0)) {
    return {
      file,
      state: "metadata_missing",
      stateMessage: "assembly_meta is missing or incomplete. The viewer is fail-closed.",
      modelId: params.manifest?.model_id ?? null,
      modelUrl: file.gltfUrl,
      contentUrl: file.originalUrl,
      previewUrls: file.previewUrls,
      nodes,
      occurrenceCount,
    };
  }

  return {
    file,
    state: "ready",
    stateMessage: "Viewer data is ready.",
    modelId: params.manifest?.model_id ?? null,
    modelUrl: file.gltfUrl,
    contentUrl: file.originalUrl || file.previewUrl,
    previewUrls: file.previewUrls,
    nodes,
    occurrenceCount,
  };
}
