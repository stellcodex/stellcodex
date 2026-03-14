"use client";

import { useCallback, useEffect, useState } from "react";
import { getProjects } from "@/lib/api/projects";
import type { ProjectSummary } from "@/lib/contracts/projects";
import { mapProjectSummary } from "@/lib/mappers/projectMappers";

export function useProjects() {
  const [data, setData] = useState<ProjectSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const payload = await getProjects();
      setData(Array.isArray(payload) ? payload.map((item) => mapProjectSummary(item)) : []);
    } catch (nextError) {
      setError(nextError instanceof Error ? nextError.message : "Projects could not be loaded.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  return { data, loading, error, refresh };
}
