"use client";

import * as React from "react";

import { getProject } from "@/lib/api/projects";
import { mapProjectRecord } from "@/lib/mappers/projectMappers";

export function useProjectDetail(projectId: string) {
  const [project, setProject] = React.useState<ReturnType<typeof mapProjectRecord> | null>(null);
  const [loading, setLoading] = React.useState(true);
  const [error, setError] = React.useState<string | null>(null);

  const refresh = React.useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await getProject(projectId);
      setProject(mapProjectRecord(response));
    } catch (caughtError) {
      setError(caughtError instanceof Error ? caughtError.message : "The project could not be loaded.");
    } finally {
      setLoading(false);
    }
  }, [projectId]);

  React.useEffect(() => {
    void refresh();
  }, [refresh]);

  const workflowSummary = React.useMemo(() => {
    if (!project) return null;
    return {
      readyCount: project.files.filter((file) => file.status === "ready").length,
      processingCount: project.files.filter((file) => ["queued", "processing", "running"].includes(file.status)).length,
      failedCount: project.files.filter((file) => file.status === "failed").length,
    };
  }, [project]);

  return { project, workflowSummary, loading, error, refresh };
}
