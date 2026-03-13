"use client";

import { useCallback, useEffect, useState } from "react";
import { listFiles } from "@/lib/api/files";
import { mapFileSummary } from "@/lib/mappers/fileMappers";
import type { FileSummary } from "@/lib/contracts/files";

type FilesPayload = {
  items?: unknown[];
};

export function useFilesIndex() {
  const [data, setData] = useState<FileSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const payload = (await listFiles(1, 100)) as FilesPayload | null;
      const items = Array.isArray(payload?.items) ? payload.items : [];
      setData(items.map((item) => mapFileSummary(item)));
    } catch (nextError) {
      setError(nextError instanceof Error ? nextError.message : "Files could not be loaded.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  return { data, loading, error, refresh };
}
