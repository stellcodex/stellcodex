"use client";

import { useCallback, useEffect, useState } from "react";
import { getFile, getFileStatus, getFileVersions } from "@/lib/api/files";
import type { FileSummary, FileVersionSummary } from "@/lib/contracts/files";
import { buildFileTimeline, mapFileSummary, mapFileVersions } from "@/lib/mappers/fileMappers";
import { getDfmReport } from "@/lib/api/dfm";
import { mapDfmReport } from "@/lib/mappers/dfmMappers";
import { getSession } from "@/lib/api/orchestrator";

export function useFileDetail(fileId: string) {
  const [file, setFile] = useState<FileSummary | null>(null);
  const [versions, setVersions] = useState<FileVersionSummary[]>([]);
  const [timeline, setTimeline] = useState<ReturnType<typeof buildFileTimeline>>([]);
  const [workflow, setWorkflow] = useState<Record<string, unknown> | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [filePayload, versionPayload, statusPayload, sessionPayload, dfmPayload] = await Promise.all([
        getFile(fileId),
        getFileVersions(fileId),
        getFileStatus(fileId),
        getSession(fileId).catch(() => null),
        getDfmReport(fileId).catch(() => null),
      ]);
      const mappedFile = mapFileSummary(filePayload);
      const nextWorkflow = sessionPayload && typeof sessionPayload === "object" ? (sessionPayload as Record<string, unknown>) : null;
      setFile(mappedFile);
      setVersions(mapFileVersions(versionPayload));
      setWorkflow(nextWorkflow);
      setTimeline(buildFileTimeline(mappedFile, Boolean(nextWorkflow), mapDfmReport(dfmPayload).status === "ready"));
      void statusPayload;
    } catch (nextError) {
      setError(nextError instanceof Error ? nextError.message : "File could not be loaded.");
    } finally {
      setLoading(false);
    }
  }, [fileId]);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  return { file, versions, timeline, workflow, loading, error, refresh };
}
