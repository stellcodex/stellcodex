"use client";

import { useMemo, useState } from "react";
import { AppShell } from "@/components/shell/AppShell";
import { AppPage } from "@/components/shell/AppPage";
import { ErrorState } from "@/components/primitives/ErrorState";
import { LoadingSkeleton } from "@/components/primitives/LoadingSkeleton";
import { ProjectsFilters } from "@/components/projects/ProjectsFilters";
import { ProjectsTable } from "@/components/projects/ProjectsTable";
import { useProjects } from "@/lib/hooks/useProjects";

export default function ProjectsPage() {
  const { data, loading, error, refresh } = useProjects();
  const [filters, setFilters] = useState({ search: "", sort: "updated_desc" });

  const rows = useMemo(() => {
    const filtered = data.filter((project) => project.name.toLowerCase().includes(filters.search.toLowerCase()));
    if (filters.sort === "name_asc") {
      return [...filtered].sort((a, b) => a.name.localeCompare(b.name));
    }
    return [...filtered].sort((a, b) => String(b.updatedAt || "").localeCompare(String(a.updatedAt || "")));
  }, [data, filters]);

  return (
    <AppShell title="Projects" subtitle="Searchable engineering project index" breadcrumbs={[{ label: "Projects" }]}>
      <AppPage title="Projects" subtitle="Open real project records and attached files">
        <ProjectsFilters value={filters} onChange={setFilters} />
        {loading ? <LoadingSkeleton label="Loading projects" /> : null}
        {error ? <ErrorState title="Projects unavailable" description={error} retryLabel="Retry" onRetry={() => void refresh()} /> : null}
        {!loading && !error ? <ProjectsTable rows={rows} /> : null}
      </AppPage>
    </AppShell>
  );
}
