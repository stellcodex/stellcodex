import { apiFetchJson } from "@/lib/api/client";

export async function createShare(fileId: string, permission: "view" | "comment" | "download", expiresInSeconds: number) {
  return apiFetchJson("/shares", {
    method: "POST",
    body: JSON.stringify({
      file_id: fileId,
      permission,
      expires_in_seconds: expiresInSeconds,
    }),
  });
}

export async function revokeShare(shareId: string) {
  return apiFetchJson(`/shares/${encodeURIComponent(shareId)}/revoke`, {
    method: "POST",
  });
}

export async function getPublicShare(token: string) {
  return apiFetchJson(`/shares/${encodeURIComponent(token)}`, undefined, { public: true });
}
