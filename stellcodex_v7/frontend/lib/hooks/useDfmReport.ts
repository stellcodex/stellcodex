"use client";

import { useCallback, useEffect, useState } from "react";
import { getDfmReport, runDfm } from "@/lib/api/dfm";
import { mapDfmReport, mapRisks } from "@/lib/mappers/dfmMappers";

export function useDfmReport(fileId: string) {
  const [report, setReport] = useState<ReturnType<typeof mapDfmReport> | null>(null);
  const [risks, setRisks] = useState<ReturnType<typeof mapRisks>>([]);
  const [loading, setLoading] = useState(true);
  const [running, setRunning] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const payload = await getDfmReport(fileId);
      setReport(mapDfmReport(payload));
      setRisks(mapRisks(payload));
    } catch (nextError) {
      setError(nextError instanceof Error ? nextError.message : "DFM report could not be loaded.");
    } finally {
      setLoading(false);
    }
  }, [fileId]);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  const rerun = useCallback(async () => {
    setRunning(true);
    try {
      await runDfm(fileId);
      await refresh();
    } finally {
      setRunning(false);
    }
  }, [fileId, refresh]);

  return { report, risks, loading, error, running, refresh, rerun };
}
