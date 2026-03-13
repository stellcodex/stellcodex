"use client";

import { useCallback, useEffect, useState } from "react";
import { ApiError } from "@/lib/api/errors";
import { createShare, getPublicShare, revokeShare } from "@/lib/api/shares";
import { listFiles, listFileShares } from "@/lib/api/files";
import type { PublicShareSummary, ShareSummary } from "@/lib/contracts/shares";
import { mapFileSummary } from "@/lib/mappers/fileMappers";
import { mapPublicShare, mapPublicShareStatus, mapShareSummary } from "@/lib/mappers/shareMappers";

type ItemsPayload = {
  items?: unknown[];
};

export function useShares(fileId?: string) {
  const [data, setData] = useState<ShareSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      if (fileId) {
        const payload = ((await listFileShares(fileId).catch(() => ({ items: [] }))) as ItemsPayload | null);
        const shares = Array.isArray(payload?.items) ? payload.items : [];
        setData(shares.map((share: unknown) => mapShareSummary(share, fileId)));
        return;
      }

      const fileList = (await listFiles(1, 50)) as ItemsPayload | null;
      const items = Array.isArray(fileList?.items) ? fileList.items : [];
      const allShares = await Promise.all(
        items.map(async (item: unknown) => {
          const file = mapFileSummary(item);
          const payload = ((await listFileShares(file.fileId).catch(() => ({ items: [] }))) as ItemsPayload | null);
          const shares = Array.isArray(payload?.items) ? payload.items : [];
          return shares.map((share: unknown) => mapShareSummary(share, file.fileName));
        })
      );
      setData(allShares.flat());
    } catch (nextError) {
      setError(nextError instanceof Error ? nextError.message : "Shares could not be loaded.");
    } finally {
      setLoading(false);
    }
  }, [fileId]);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  const create = useCallback(async (nextFileId: string, permission: "view" | "comment" | "download", expiresInSeconds: number) => {
    const payload = await createShare(nextFileId, permission, expiresInSeconds);
    await refresh();
    return payload;
  }, [refresh]);

  const revoke = useCallback(async (shareId: string) => {
    await revokeShare(shareId);
    await refresh();
  }, [refresh]);

  return { data, loading, error, refresh, create, revoke };
}

export function usePublicShare(token: string) {
  const [data, setData] = useState<PublicShareSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const payload = await getPublicShare(token);
      setData(mapPublicShare(token, payload));
    } catch (nextError) {
      if (nextError instanceof ApiError) {
        if (nextError.status === 410) {
          setData(mapPublicShareStatus(token, "expired"));
          setError(null);
        } else if (nextError.status === 403) {
          setData(mapPublicShareStatus(token, "revoked"));
          setError(null);
        } else if (nextError.status === 401) {
          setData(mapPublicShareStatus(token, "forbidden"));
          setError(null);
        } else {
          setData(mapPublicShareStatus(token, "invalid"));
          setError(nextError.safeMessage);
        }
      } else {
        setError(nextError instanceof Error ? nextError.message : "Share could not be loaded.");
      }
    } finally {
      setLoading(false);
    }
  }, [token]);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  return { data, loading, error, refresh };
}
