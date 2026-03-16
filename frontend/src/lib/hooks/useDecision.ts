"use client";

import * as React from "react";

import { getDecision } from "@/lib/api/orchestrator";
import { mapDecisionRecord } from "@/lib/mappers/orchestratorMappers";

export function useDecision(params: { fileId?: string; sessionId?: string }) {
  const fileId = params.fileId;
  const sessionId = params.sessionId;
  const [decision, setDecision] = React.useState<ReturnType<typeof mapDecisionRecord> | null>(null);
  const [loading, setLoading] = React.useState(Boolean(fileId || sessionId));
  const [error, setError] = React.useState<string | null>(null);

  const refresh = React.useCallback(async () => {
    if (!fileId && !sessionId) {
      setDecision(null);
      setLoading(false);
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const response = await getDecision({ fileId, sessionId });
      setDecision(mapDecisionRecord(response));
    } catch (caughtError) {
      setError(caughtError instanceof Error ? caughtError.message : "Decision data could not be loaded.");
    } finally {
      setLoading(false);
    }
  }, [fileId, sessionId]);

  React.useEffect(() => {
    void refresh();
  }, [refresh]);

  return { decision, loading, error, refresh };
}
