"use client";

import { useCallback, useEffect, useState } from "react";
import { getDecision } from "@/lib/api/orchestrator";
import { mapDecisionSummary } from "@/lib/mappers/orchestratorMappers";

export function useDecision(sessionId?: string | null) {
  const [data, setData] = useState<ReturnType<typeof mapDecisionSummary> | null>(null);
  const [loading, setLoading] = useState(Boolean(sessionId));
  const [error, setError] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    if (!sessionId) {
      setData(null);
      setLoading(false);
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const payload = await getDecision(sessionId);
      setData(mapDecisionSummary(payload));
    } catch (nextError) {
      setError(nextError instanceof Error ? nextError.message : "Decision could not be loaded.");
    } finally {
      setLoading(false);
    }
  }, [sessionId]);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  return { data, loading, error, refresh };
}
