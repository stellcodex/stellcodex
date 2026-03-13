"use client";

import { useCallback, useEffect, useState } from "react";
import { getProject } from "@/lib/api/projects";
import type { ProjectDetail } from "@/lib/contracts/projects";
import { mapProjectDetail } from "@/lib/mappers/projectMappers";

export function useProjectDetail(projectId: string) {
  const [data, setData] = useState<ProjectDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const payload = await getProject(projectId);
      setData(mapProjectDetail(payload));
    } catch (nextError) {
      setError(nextError instanceof Error ? nextError.message : "Project could not be loaded.");
    } finally {
      setLoading(false);
    }
  }, [projectId]);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  return { data, loading, error, refresh };
}
