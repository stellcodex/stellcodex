import type { PublicShareSummary, ShareSummary } from "@/lib/contracts/shares";

type RawRecord = Record<string, unknown>;

function shareStatus(expiresAt?: string | null, revokedAt?: string | null): ShareSummary["status"] {
  if (revokedAt) return "revoked";
  if (!expiresAt) return "unknown";
  const expires = new Date(expiresAt);
  if (Number.isNaN(expires.getTime())) return "unknown";
  return expires.getTime() < Date.now() ? "expired" : "active";
}

export function mapShareSummary(input: unknown, targetName: string, targetType: "file" | "project" = "file"): ShareSummary {
  const row = (input && typeof input === "object" ? input : {}) as RawRecord;
  const token = typeof row.token === "string" ? row.token : null;
  const expiresAt = typeof row.expires_at === "string" ? row.expires_at : null;
  return {
    shareId: typeof row.id === "string" ? row.id : token || "unknown",
    targetType,
    targetName,
    permission: typeof row.permission === "string" ? row.permission : "view",
    createdAt: typeof row.created_at === "string" ? row.created_at : null,
    expiresAt,
    status: shareStatus(expiresAt, typeof row.revoked_at === "string" ? row.revoked_at : null),
    publicUrl: token ? `/s/${token}` : null,
    token,
  };
}

export function mapPublicShare(token: string, input: unknown): PublicShareSummary {
  const row = (input && typeof input === "object" ? input : {}) as RawRecord;
  return {
    token,
    fileId: typeof row.file_id === "string" ? row.file_id : null,
    fileName: typeof row.original_filename === "string" ? row.original_filename : "Shared file",
    status: "valid",
    permission: typeof row.permission === "string" ? row.permission : null,
    canDownload: Boolean(row.can_download),
    expiresAt: typeof row.expires_at === "string" ? row.expires_at : null,
    contentType: typeof row.content_type === "string" ? row.content_type : null,
    viewerUrl:
      (typeof row.gltf_url === "string" && row.gltf_url) ||
      (typeof row.original_url === "string" && row.original_url) ||
      null,
    downloadUrl: Boolean(row.can_download) && typeof row.original_url === "string" ? row.original_url : null,
  };
}
