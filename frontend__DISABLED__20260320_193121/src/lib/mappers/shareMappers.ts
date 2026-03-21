import type { RawPublicShare, RawShare } from "@/lib/contracts/shares";
import type { PublicShareRecord, ShareRecord } from "@/lib/contracts/ui";

function resolveShareStatus(expiresAt: string, revoked: boolean) {
  if (revoked) return "revoked" as const;
  return new Date(expiresAt).getTime() < Date.now() ? "expired" as const : "active" as const;
}

export function mapPublicShareTerminalState(statusCode: number) {
  if (statusCode === 410) return "expired" as const;
  if (statusCode === 403) return "revoked" as const;
  return "invalid" as const;
}

export function mapShareRecord(input: RawShare, baseUrl: string, fileId?: string, revoked = false): ShareRecord {
  return {
    shareId: input.id,
    token: input.token,
    permission: input.permission,
    expiresAt: input.expires_at,
    publicUrl: `${baseUrl}/s/${input.token}`,
    status: resolveShareStatus(input.expires_at, revoked),
    fileId,
  };
}

export function mapPublicShareRecord(input: RawPublicShare): PublicShareRecord {
  return {
    permission: input.permission,
    canView: input.can_view,
    canDownload: input.can_download,
    expiresAt: input.expires_at,
    contentType: input.content_type,
    originalFilename: input.original_filename,
    sizeBytes: input.size_bytes,
    gltfUrl: input.gltf_url ?? null,
    originalUrl: input.original_url ?? null,
  };
}
