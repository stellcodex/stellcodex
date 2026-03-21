"use client";

import * as React from "react";

import { Button } from "@/components/primitives/Button";
import { Card } from "@/components/primitives/Card";
import { Input } from "@/components/primitives/Input";
import { Select } from "@/components/primitives/Select";
import { PageHeader } from "@/components/shell/PageHeader";
import { RouteErrorState } from "@/components/states/RouteErrorState";
import { RouteLoadingState } from "@/components/states/RouteLoadingState";
import { createProject } from "@/lib/api/projects";
import { useProjects } from "@/lib/hooks/useProjects";

import { ProjectTable } from "./ProjectTable";

export function ProjectsScreen() {
  const { filters, projects, loading, error, refresh } = useProjects();
  const [draftName, setDraftName] = React.useState("");
  const [busy, setBusy] = React.useState(false);

  async function handleCreateProject() {
    if (!draftName.trim()) return;
    setBusy(true);
    try {
      await createProject(draftName.trim());
      setDraftName("");
      await refresh();
    } finally {
      setBusy(false);
    }
  }

  if (loading) return <RouteLoadingState title="Loading projects" />;
  if (error) return <RouteErrorState actionLabel="Retry" description={error} onAction={() => void refresh()} title="Projects unavailable" />;

  return (
    <div className="space-y-6">
      <PageHeader subtitle="Search, sort, and open projects backed by the current backend project contract." title="Projects" />
      <Card description="Create a project and bind future uploads to it." title="Create project">
        <div className="flex flex-col gap-3 md:flex-row">
          <Input onChange={(event) => setDraftName(event.target.value)} placeholder="Tooling package" value={draftName} />
          <Button onClick={() => void handleCreateProject()} variant="primary">
            {busy ? "Creating..." : "Create"}
          </Button>
        </div>
      </Card>
      <Card description="Filter and sort active project workspaces." title="Project list">
        <div className="mb-4 grid gap-3 md:grid-cols-3">
          <Input onChange={(event) => filters.setProjectSearch(event.target.value)} placeholder="Search name or project ID" value={filters.projectSearch} />
          <Select onChange={(event) => filters.setProjectStatus(event.target.value)} value={filters.projectStatus}>
            <option value="all">All statuses</option>
            <option value="ready">Ready</option>
            <option value="failed">Failed</option>
            <option value="queued">Queued</option>
            <option value="processing">Processing</option>
          </Select>
          <Select onChange={(event) => filters.setSortMode(event.target.value as "updated_desc" | "updated_asc" | "name_asc")} value={filters.sortMode}>
            <option value="updated_desc">Updated desc</option>
            <option value="updated_asc">Updated asc</option>
            <option value="name_asc">Name asc</option>
          </Select>
        </div>
        <ProjectTable projects={projects} />
      </Card>
    </div>
  );
}
