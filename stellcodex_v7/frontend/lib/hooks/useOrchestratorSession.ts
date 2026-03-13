"use client";

import { useCallback, useEffect, useState } from "react";
import { advanceWorkflow, getSession, startOrchestrator } from "@/lib/api/orchestrator";
import { mapDecisionSummary, mapOrchestratorState } from "@/lib/mappers/orchestratorMappers";

export function useOrchestratorSession(fileId: string) {
  const [state, setState] = useState<ReturnType<typeof mapOrchestratorState> | null>(null);
  const [decision, setDecision] = useState<ReturnType<typeof mapDecisionSummary> | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const payload = await getSession(fileId);
      setState(mapOrchestratorState(payload));
      setDecision(mapDecisionSummary(payload));
    } catch (nextError) {
      setError(nextError instanceof Error ? nextError.message : "Workflow state could not be loaded.");
    } finally {
      setLoading(false);
    }
  }, [fileId]);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  const start = useCallback(async () => {
    await startOrchestrator(fileId);
    await refresh();
  }, [fileId, refresh]);

  const advance = useCallback(async (approve = false, note?: string) => {
    await advanceWorkflow(fileId, approve, note);
    await refresh();
  }, [fileId, refresh]);

  return { state, decision, loading, error, refresh, start, advance };
}
