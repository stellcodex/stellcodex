import { NextResponse } from "next/server";
import {
  apiBase,
  extOf,
  mapLegacyEngine,
  mapLegacyKind,
  mapLegacyProgress,
  mapLegacyStage,
  mapLegacyStatusFromState,
  readErrorMessage,
  readPayload,
  upstreamHeaders,
} from "@/app/api/_lib/upstream";

function nowIso() {
  return new Date().toISOString();
}

export async function GET(req: Request, { params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const url = new URL(req.url);

  if (url.searchParams.get("download") === "1") {
    const upstream = await fetch(`${apiBase()}/files/${encodeURIComponent(id)}/content`, {
      headers: upstreamHeaders(req),
      cache: "no-store",
    });
    if (!upstream.ok) {
      const payload = await readPayload(upstream);
      return NextResponse.json(
        { error: readErrorMessage(payload, "Dosya indirilemedi.") },
        { status: upstream.status }
      );
    }
    const headers = new Headers();
    headers.set("Content-Type", upstream.headers.get("content-type") || "application/octet-stream");
    headers.set(
      "Content-Disposition",
      upstream.headers.get("content-disposition") || `attachment; filename="${encodeURIComponent(id)}"`
    );
    return new Response(upstream.body, { status: 200, headers });
  }

  const authHeaders = upstreamHeaders(req);
  const detailUpstream = await fetch(`${apiBase()}/files/${encodeURIComponent(id)}`, {
    headers: authHeaders,
    cache: "no-store",
  });
  const detailPayload = await readPayload(detailUpstream);
  if (!detailUpstream.ok) {
    return NextResponse.json(
      { error: readErrorMessage(detailPayload, "Dosya bulunamadı.") },
      { status: detailUpstream.status }
    );
  }
  const detail =
    detailPayload && typeof detailPayload === "object" ? (detailPayload as Record<string, unknown>) : {};

  const statusUpstream = await fetch(`${apiBase()}/files/${encodeURIComponent(id)}/status`, {
    headers: authHeaders,
    cache: "no-store",
  });
  const statusPayload = await readPayload(statusUpstream);
  const statusData =
    statusUpstream.ok && statusPayload && typeof statusPayload === "object"
      ? (statusPayload as Record<string, unknown>)
      : null;

  const fileId = typeof detail.file_id === "string" ? detail.file_id : id;
  const name =
    typeof detail.original_name === "string" && detail.original_name.trim()
      ? detail.original_name
      : "unnamed";
  const contentType = typeof detail.content_type === "string" ? detail.content_type : "application/octet-stream";
  const ext = extOf(name);
  const legacyKind = mapLegacyKind(detail.kind, contentType, name);
  const legacyEngine = mapLegacyEngine(detail.kind, contentType, name);
  const stage = mapLegacyStage(statusData?.stage, statusData?.state || detail.status);
  const status = mapLegacyStatusFromState(statusData?.state || detail.status);
  const progress = mapLegacyProgress(statusData?.progress_percent, statusData?.state || detail.status);

  return NextResponse.json({
    file: {
      id: fileId,
      projectId: "default",
      folderId: "root",
      name,
      ext,
      mime: contentType,
      sizeBytes: typeof detail.size_bytes === "number" ? Math.max(0, Math.round(detail.size_bytes)) : 0,
      kind: legacyKind,
      engine: legacyEngine,
      storageKey: `file/${fileId}`,
      createdAt: typeof detail.created_at === "string" ? detail.created_at : nowIso(),
      previewUrl:
        typeof detail.preview_url === "string"
          ? detail.preview_url
          : typeof detail.thumbnail_url === "string"
          ? detail.thumbnail_url
          : null,
      downloadUrl: `/api/file/${encodeURIComponent(fileId)}?download=1`,
      archiveEntries: null,
      extractedFolderId: null,
    },
    previewUrl:
      typeof detail.preview_url === "string"
        ? detail.preview_url
        : typeof detail.thumbnail_url === "string"
        ? detail.thumbnail_url
        : null,
    downloadUrl: `/api/file/${encodeURIComponent(fileId)}?download=1`,
    inFolder: null,
    job: {
      id: `file:${fileId}`,
      fileId,
      status,
      stage,
      progress,
      error: typeof detail.error === "string" ? detail.error : null,
      createdAt: typeof detail.created_at === "string" ? detail.created_at : nowIso(),
      updatedAt: nowIso(),
    },
  });
}
