import type { RawPublicShare, RawShare, RawShareList } from "@/lib/contracts/shares";

import { apiJson } from "./fetch";
import { getAuthHeaders } from "./session";

export async function createShare(fileId: string, permission = "view", expiresInSeconds = 7 * 24 * 60 * 60) {
  return apiJson<RawShare>("/shares", {
    method: "POST",
    headers: await getAuthHeaders({ headers: { "Content-Type": "application/json" } }),
    body: JSON.stringify({
      file_id: fileId,
      permission,
      expires_in_seconds: expiresInSeconds,
    }),
  });
}

export async function listFileShares(fileId: string) {
  return apiJson<RawShareList>(`/files/${encodeURIComponent(fileId)}/shares`, {
    headers: await getAuthHeaders(),
  });
}

export async function revokeShare(shareId: string) {
  return apiJson<{ status: string }>(`/shares/${encodeURIComponent(shareId)}/revoke`, {
    method: "POST",
    headers: await getAuthHeaders(),
  });
}

export async function resolvePublicShare(token: string) {
  return apiJson<RawPublicShare>(`/s/${encodeURIComponent(token)}`);
}
