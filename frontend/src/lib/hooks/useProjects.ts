"use client";

import * as React from "react";

import { listProjects } from "@/lib/api/projects";
import { mapProjectRecord } from "@/lib/mappers/projectMappers";
import { useFiltersStore } from "@/lib/stores/filtersStore";

export function useProjects() {
  const [projects, setProjects] = React.useState<ReturnType<typeof mapProjectRecord>[]>([]);
  const [loading, setLoading] = React.useState(true);
  const [error, setError] = React.useState<string | null>(null);
  const { projectSearch, projectStatus, setProjectSearch, setProjectStatus, setSortMode, sortMode } = useFiltersStore();
  const deferredSearch = React.useDeferredValue(projectSearch);

  const refresh = React.useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const rows = await listProjects();
      setProjects(rows.map(mapProjectRecord));
    } catch (caughtError) {
      setError(caughtError instanceof Error ? caughtError.message : "Projects could not be loaded.");
    } finally {
      setLoading(false);
    }
  }, []);

  React.useEffect(() => {
    void refresh();
  }, [refresh]);

  const filteredProjects = React.useMemo(() => {
    const normalizedSearch = deferredSearch.trim().toLowerCase();
    const next = projects.filter((project) => {
      const matchesSearch =
        normalizedSearch.length === 0 ||
        project.name.toLowerCase().includes(normalizedSearch) ||
        project.projectId.toLowerCase().includes(normalizedSearch);
      const matchesStatus =
        projectStatus === "all" ||
        project.files.some((file) => file.status.toLowerCase() === projectStatus.toLowerCase());
      return matchesSearch && matchesStatus;
    });

    next.sort((left, right) => {
      if (sortMode === "name_asc") return left.name.localeCompare(right.name);
      const leftValue = left.updatedAt ? new Date(left.updatedAt).getTime() : 0;
      const rightValue = right.updatedAt ? new Date(right.updatedAt).getTime() : 0;
      return sortMode === "updated_asc" ? leftValue - rightValue : rightValue - leftValue;
    });
    return next;
  }, [deferredSearch, projectStatus, projects, sortMode]);

  return {
    projects: filteredProjects,
    loading,
    error,
    refresh,
    filters: {
      projectSearch,
      projectStatus,
      sortMode,
      setProjectSearch,
      setProjectStatus,
      setSortMode,
    },
  };
}
