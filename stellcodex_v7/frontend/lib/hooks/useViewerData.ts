"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { getFile, getFileManifest } from "@/lib/api/files";
import { getDfmReport } from "@/lib/api/dfm";
import { getSession } from "@/lib/api/orchestrator";
import { mapFileSummary } from "@/lib/mappers/fileMappers";
import { mapViewerSummary } from "@/lib/mappers/viewerMappers";
import { mapDfmReport, mapRisks } from "@/lib/mappers/dfmMappers";
import { mapDecisionSummary, mapOrchestratorState } from "@/lib/mappers/orchestratorMappers";

export function useViewerData(fileId: string) {
  const [file, setFile] = useState<ReturnType<typeof mapFileSummary> | null>(null);
  const [viewer, setViewer] = useState<ReturnType<typeof mapViewerSummary> | null>(null);
  const [state, setState] = useState<ReturnType<typeof mapOrchestratorState> | null>(null);
  const [decision, setDecision] = useState<ReturnType<typeof mapDecisionSummary> | null>(null);
  const [dfm, setDfm] = useState<ReturnType<typeof mapDfmReport> | null>(null);
  const [risks, setRisks] = useState<ReturnType<typeof mapRisks>>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [filePayload, manifestPayload, sessionPayload, dfmPayload] = await Promise.all([
        getFile(fileId),
        getFileManifest(fileId).catch(() => null),
        getSession(fileId).catch(() => null),
        getDfmReport(fileId).catch(() => null),
      ]);
      const mappedFile = mapFileSummary(filePayload);
      setFile(mappedFile);
      setViewer(mapViewerSummary(mappedFile, manifestPayload));
      setState(sessionPayload ? mapOrchestratorState(sessionPayload) : null);
      setDecision(sessionPayload ? mapDecisionSummary(sessionPayload) : null);
      setDfm(mapDfmReport(dfmPayload));
      setRisks(mapRisks(dfmPayload));
    } catch (nextError) {
      setError(nextError instanceof Error ? nextError.message : "Viewer data could not be loaded.");
    } finally {
      setLoading(false);
    }
  }, [fileId]);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  const activity = useMemo(() => {
    const items = [];
    if (file?.createdAt) {
      items.push({ id: "uploaded", timestamp: file.createdAt, type: "upload", description: "File uploaded" });
    }
    if (viewer?.status === "ready" && file?.updatedAt) {
      items.push({ id: "viewer", timestamp: file.updatedAt, type: "viewer", description: "Viewer ready" });
    }
    if (state?.updatedAt) {
      items.push({ id: "state", timestamp: state.updatedAt, type: "state", description: `Workflow at ${state.stateCode}` });
    }
    return items;
  }, [file, viewer, state]);

  return { file, viewer, state, decision, dfm, risks, activity, loading, error, refresh };
}
