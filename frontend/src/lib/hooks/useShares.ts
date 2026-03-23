"use client";

import * as React from "react";

import { listFiles } from "@/lib/api/files";
import { createShare, listFileShares, revokeShare } from "@/lib/api/shares";
import { mapFileRecord } from "@/lib/mappers/fileMappers";
import { mapShareRecord } from "@/lib/mappers/shareMappers";

export function useShares(fileId?: string) {
  const [shares, setShares] = React.useState<ReturnType<typeof mapShareRecord>[]>([]);
  const [loading, setLoading] = React.useState(true);
  const [error, setError] = React.useState<string | null>(null);
  const [revokedIds, setRevokedIds] = React.useState<string[]>([]);

  const refresh = React.useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const origin = typeof window !== "undefined" ? window.location.origin : "";
      if (fileId) {
        const response = await listFileShares(fileId);
        setShares(response.items.map((item) => mapShareRecord(item, origin, fileId, revokedIds.includes(item.id))));
      } else {
        const files = (await listFiles()).map(mapFileRecord);
        const grouped = await Promise.all(
          files.map(async (file) => {
            const response = await listFileShares(file.fileId).catch(() => ({ items: [] }));
            return response.items.map((item) => mapShareRecord(item, origin, file.fileId, revokedIds.includes(item.id)));
          }),
        );
        setShares(grouped.flat());
      }
    } catch (caughtError) {
      setError(caughtError instanceof Error ? caughtError.message : "Shares could not be loaded.");
    } finally {
      setLoading(false);
    }
  }, [fileId, revokedIds]);

  React.useEffect(() => {
    void refresh();
  }, [refresh]);

  async function create(fileIdValue: string, permission: string, expiresInSeconds: number) {
    const origin = typeof window !== "undefined" ? window.location.origin : "";
    const created = await createShare(fileIdValue, permission, expiresInSeconds);
    const mapped = mapShareRecord(created, origin, fileIdValue);
    setShares((current) => [mapped, ...current]);
    return mapped;
  }

  async function revoke(shareId: string) {
    await revokeShare(shareId);
    setRevokedIds((current) => [...current, shareId]);
    setShares((current) =>
      current.map((item) => (item.shareId === shareId ? { ...item, status: "revoked" } : item)),
    );
  }

  async function copyLink(share: { publicUrl: string }) {
    await navigator.clipboard.writeText(share.publicUrl);
  }

  function openLink(share: { publicUrl: string }) {
    window.open(share.publicUrl, "_blank", "noopener,noreferrer");
  }

  return { shares, loading, error, refresh, create, revoke, copyLink, openLink };
}
