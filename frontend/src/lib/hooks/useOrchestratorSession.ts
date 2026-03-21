"use client";

import * as React from "react";

import { getDecision, startOrchestrator } from "@/lib/api/orchestrator";
import { mapDecisionRecord } from "@/lib/mappers/orchestratorMappers";

export function useOrchestratorSession(fileId: string) {
  const [decision, setDecision] = React.useState<ReturnType<typeof mapDecisionRecord> | null>(null);
  const [loading, setLoading] = React.useState(true);
  const [error, setError] = React.useState<string | null>(null);

  const refresh = React.useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const initial = await startOrchestrator(fileId).catch(() => null);
      const response = initial ?? (await getDecision({ fileId }));
      setDecision(mapDecisionRecord(response));
    } catch (caughtError) {
      setError(caughtError instanceof Error ? caughtError.message : "The orchestrator session could not be loaded.");
    } finally {
      setLoading(false);
    }
  }, [fileId]);

  React.useEffect(() => {
    void refresh();
  }, [refresh]);

  return { decision, loading, error, refresh };
}
