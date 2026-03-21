"use client";

import * as React from "react";

import { getFile } from "@/lib/api/files";
import { getDecision } from "@/lib/api/orchestrator";
import { listProjects } from "@/lib/api/projects";
import { listFileShares } from "@/lib/api/shares";
import { mapFileRecord } from "@/lib/mappers/fileMappers";
import { mapDecisionRecord } from "@/lib/mappers/orchestratorMappers";
import { mapProjectRecord } from "@/lib/mappers/projectMappers";
import { mapShareRecord } from "@/lib/mappers/shareMappers";

export function useFileDetail(fileId: string) {
  const [file, setFile] = React.useState<ReturnType<typeof mapFileRecord> | null>(null);
  const [decision, setDecision] = React.useState<ReturnType<typeof mapDecisionRecord> | null>(null);
  const [projectName, setProjectName] = React.useState<string | null>(null);
  const [shares, setShares] = React.useState<ReturnType<typeof mapShareRecord>[]>([]);
  const [loading, setLoading] = React.useState(true);
  const [error, setError] = React.useState<string | null>(null);

  const refresh = React.useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [fileResponse, decisionResponse, projectResponses, shareResponse] = await Promise.all([
        getFile(fileId),
        getDecision({ fileId }).catch(() => null),
        listProjects().catch(() => []),
        listFileShares(fileId).catch(() => ({ items: [] })),
      ]);

      setFile(mapFileRecord(fileResponse));
      if (decisionResponse) setDecision(mapDecisionRecord(decisionResponse));

      const mappedProjects = projectResponses.map(mapProjectRecord);
      const containingProject = mappedProjects.find((project) => project.files.some((item) => item.fileId === fileId));
      setProjectName(containingProject?.name ?? null);

      const origin = typeof window !== "undefined" ? window.location.origin : "";
      setShares(shareResponse.items.map((item) => mapShareRecord(item, origin, fileId)));
    } catch (caughtError) {
      setError(caughtError instanceof Error ? caughtError.message : "The file could not be loaded.");
    } finally {
      setLoading(false);
    }
  }, [fileId]);

  React.useEffect(() => {
    void refresh();
  }, [refresh]);

  return {
    file,
    decision,
    projectName,
    shares,
    versionsSupported: false,
    loading,
    error,
    refresh,
  };
}
