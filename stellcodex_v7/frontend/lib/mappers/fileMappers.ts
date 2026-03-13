import type { FileSummary, FileTimelineEvent, FileVersionSummary } from "@/lib/contracts/files";
import { isReadyStatus } from "@/lib/utils/status";

type RawRecord = Record<string, unknown>;

export function mapFileSummary(input: unknown): FileSummary {
  const row = (input && typeof input === "object" ? input : {}) as RawRecord;
  const status = typeof row.status === "string" ? row.status : "unknown";
  const kind = typeof row.kind === "string" ? row.kind : null;
  return {
    fileId: typeof row.file_id === "string" ? row.file_id : "",
    fileName:
      (typeof row.original_name === "string" && row.original_name) ||
      (typeof row.original_filename === "string" && row.original_filename) ||
      "Untitled file",
    mimeType: typeof row.content_type === "string" ? row.content_type : null,
    sizeBytes: typeof row.size_bytes === "number" ? row.size_bytes : null,
    status,
    kind,
    mode: typeof row.mode === "string" ? row.mode : null,
    viewerReady: Boolean(row.gltf_url) || kind === "2d" || kind === "doc" || kind === "image" || isReadyStatus(status),
    gltfUrl: typeof row.gltf_url === "string" ? row.gltf_url : null,
    originalUrl: typeof row.original_url === "string" ? row.original_url : null,
    thumbnailUrl: typeof row.thumbnail_url === "string" ? row.thumbnail_url : null,
    previewUrls: Array.isArray(row.preview_urls)
      ? row.preview_urls.filter((value): value is string => typeof value === "string")
      : [],
    createdAt: typeof row.created_at === "string" ? row.created_at : null,
    updatedAt: typeof row.updated_at === "string" ? row.updated_at : null,
    partCount: typeof row.part_count === "number" ? row.part_count : null,
    extractionStatus: typeof row.extraction_status === "string" ? row.extraction_status : null,
    error: typeof row.error === "string" ? row.error : null,
  };
}

export function mapFileVersions(input: unknown): FileVersionSummary[] {
  const payload = (input && typeof input === "object" ? input : {}) as RawRecord;
  const versions = Array.isArray(payload.versions) ? payload.versions : [];
  return versions.map((row, index) => {
    const data = (row && typeof row === "object" ? row : {}) as RawRecord;
    const versionNo = typeof data.version_no === "number" ? data.version_no : index + 1;
    return {
      versionId: `version-${versionNo}`,
      label: `v${versionNo}`,
      createdAt: typeof data.created_at === "string" ? data.created_at : null,
      status: typeof data.status === "string" ? data.status : null,
      isCurrent: index === versions.length - 1,
    };
  });
}

export function buildFileTimeline(file: FileSummary, decisionAvailable?: boolean, dfmReady?: boolean): FileTimelineEvent[] {
  const events: FileTimelineEvent[] = [
    { id: "uploaded", label: "Uploaded", timestamp: file.createdAt, status: "done" },
  ];
  if (file.viewerReady) {
    events.push({ id: "viewer", label: "Viewer ready", timestamp: file.updatedAt, status: "done" });
  }
  if (decisionAvailable) {
    events.push({ id: "decision", label: "Decision available", timestamp: file.updatedAt, status: "done" });
  }
  if (dfmReady) {
    events.push({ id: "dfm", label: "DFM ready", timestamp: file.updatedAt, status: "done" });
  }
  if (file.status === "failed") {
    events.push({ id: "failed", label: "Failed", timestamp: file.updatedAt, status: "failed" });
  }
  return events;
}
