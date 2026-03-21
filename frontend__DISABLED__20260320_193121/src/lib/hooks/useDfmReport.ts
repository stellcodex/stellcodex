"use client";

import * as React from "react";

import { getDfmReport } from "@/lib/api/dfm";
import { mapDfmRecord } from "@/lib/mappers/orchestratorMappers";

export function useDfmReport(fileId: string) {
  const [report, setReport] = React.useState<ReturnType<typeof mapDfmRecord> | null>(null);
  const [loading, setLoading] = React.useState(true);
  const [error, setError] = React.useState<string | null>(null);

  const refresh = React.useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await getDfmReport(fileId);
      setReport(mapDfmRecord(response));
    } catch (caughtError) {
      setError(caughtError instanceof Error ? caughtError.message : "The DFM report could not be loaded.");
    } finally {
      setLoading(false);
    }
  }, [fileId]);

  React.useEffect(() => {
    void refresh();
  }, [refresh]);

  return { report, loading, error, refresh, rerunSupported: false };
}
