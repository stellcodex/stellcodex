import { NextResponse } from "next/server";
import {
  extOf,
  mapLegacyEngine,
  mapLegacyKind,
  readErrorMessage,
  readPayload,
  apiBase,
} from "@/app/api/_lib/upstream";

export async function GET(_req: Request, { params }: { params: Promise<{ token: string }> }) {
  const { token } = await params;
  const upstream = await fetch(`${apiBase()}/shares/${encodeURIComponent(token)}`, {
    cache: "no-store",
  });
  const payload = await readPayload(upstream);
  if (!upstream.ok) {
    return NextResponse.json(
      { error: readErrorMessage(payload, "Paylaşım linki bulunamadı.") },
      { status: upstream.status }
    );
  }

  const data = payload && typeof payload === "object" ? (payload as Record<string, unknown>) : {};
  const fileId = typeof data.file_id === "string" ? data.file_id : "";
  const fileName =
    typeof data.original_filename === "string" && data.original_filename.trim()
      ? data.original_filename
      : "shared-file";
  const contentType = typeof data.content_type === "string" ? data.content_type : "application/octet-stream";
  const ext = extOf(fileName);
  const kind = mapLegacyKind(undefined, contentType, fileName);
  const engine = mapLegacyEngine(undefined, contentType, fileName);
  const previewUrl =
    typeof data.gltf_url === "string"
      ? data.gltf_url
      : typeof data.original_url === "string"
      ? data.original_url
      : null;
  const downloadUrl =
    typeof data.original_url === "string"
      ? data.original_url
      : typeof data.gltf_url === "string"
      ? data.gltf_url
      : `/api/v1/share/${encodeURIComponent(token)}/content`;

  return NextResponse.json({
    file: {
      id: fileId,
      projectId: "share",
      folderId: "share",
      name: fileName,
      ext,
      mime: contentType,
      sizeBytes: typeof data.size_bytes === "number" ? Math.max(0, Math.round(data.size_bytes)) : 0,
      kind,
      engine,
      storageKey: `share/${fileId}`,
      createdAt: new Date().toISOString(),
      previewUrl,
      downloadUrl,
      archiveEntries: null,
      extractedFolderId: null,
    },
    previewUrl,
    downloadUrl,
    canView: data.can_view !== false,
    canDownload: data.can_download === true,
    expiresAt: typeof data.expires_at === "string" ? data.expires_at : null,
  });
}
