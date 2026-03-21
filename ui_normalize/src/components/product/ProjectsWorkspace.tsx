"use client";

import * as React from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";

import { Button } from "@/components/primitives/Button";
import { Card } from "@/components/primitives/Card";
import { EmptyState } from "@/components/primitives/EmptyState";
import { Input } from "@/components/primitives/Input";
import { Select } from "@/components/primitives/Select";
import { RouteErrorState } from "@/components/states/RouteErrorState";
import { RouteLoadingState } from "@/components/states/RouteLoadingState";
import { createProject } from "@/lib/api/projects";
import type { ProjectRecord } from "@/lib/contracts/ui";
import { useProjects } from "@/lib/hooks/useProjects";
import { formatDate } from "@/lib/utils";

function projectStatusCounts(project: ProjectRecord) {
  return {
    ready: project.files.filter((file) => file.status.toLowerCase() === "ready").length,
    active: project.files.filter((file) => ["queued", "processing", "running"].includes(file.status.toLowerCase())).length,
    failed: project.files.filter((file) => file.status.toLowerCase() === "failed").length,
  };
}

export function ProjectsWorkspace() {
  const router = useRouter();
  const { filters, projects, loading, error, refresh } = useProjects();
  const [draftName, setDraftName] = React.useState("");
  const [busy, setBusy] = React.useState(false);
  const [createError, setCreateError] = React.useState<string | null>(null);

  async function handleCreateProject() {
    if (!draftName.trim()) {
      setCreateError("Enter a project name before creating a workspace.");
      return;
    }

    setBusy(true);
    setCreateError(null);
    try {
      const created = await createProject(draftName.trim());
      setDraftName("");
      await refresh();
      router.push(`/projects/${encodeURIComponent(created.id)}`);
    } catch (caughtError) {
      setCreateError(caughtError instanceof Error ? caughtError.message : "Project creation failed.");
    } finally {
      setBusy(false);
    }
  }

  if (loading) return <RouteLoadingState title="Loading projects workspace" />;
  if (error) return <RouteErrorState actionLabel="Retry" description={error} onAction={() => void refresh()} title="Projects unavailable" />;

  const activeProjects = projects.filter((project) => projectStatusCounts(project).active > 0);
  const blockedProjects = projects.filter((project) => projectStatusCounts(project).failed > 0);

  return (
    <div className="mx-auto max-w-[900px] space-y-6">
      <Card
        actions={
          <Button onClick={() => void handleCreateProject()} size="sm" variant="primary">
            {busy ? "Creating..." : "Create"}
          </Button>
        }
        title="Create Project"
      >
        <div className="space-y-3">
          <Input onChange={(event) => setDraftName(event.target.value)} placeholder="Project name" value={draftName} />
          {createError ? <div className="text-sm text-[var(--foreground-default)]">{createError}</div> : null}
        </div>
      </Card>

      <Card title="Projects">
        <div className="mb-4 space-y-3">
          <Input onChange={(event) => filters.setProjectSearch(event.target.value)} placeholder="Search" value={filters.projectSearch} />
          <Select onChange={(event) => filters.setProjectStatus(event.target.value)} value={filters.projectStatus}>
            <option value="all">All statuses</option>
            <option value="ready">Ready</option>
            <option value="failed">Failed</option>
            <option value="queued">Queued</option>
            <option value="processing">Processing</option>
          </Select>
          <Select
            onChange={(event) => filters.setSortMode(event.target.value as "updated_desc" | "updated_asc" | "name_asc")}
            value={filters.sortMode}
          >
            <option value="updated_desc">Updated desc</option>
            <option value="updated_asc">Updated asc</option>
            <option value="name_asc">Name asc</option>
          </Select>
        </div>

        {projects.length === 0 ? (
          <EmptyState description="Create a project to start." title="No projects" />
        ) : (
          <div className="space-y-3">
            {projects.map((project) => {
              const counts = projectStatusCounts(project);
              return (
                <Link
                  className="block rounded-[12px] border border-[#eee] p-4 transition-colors hover:bg-[var(--background-muted)]"
                  href={`/projects/${encodeURIComponent(project.projectId)}`}
                  key={project.projectId}
                >
                  <div className="text-sm font-semibold text-[var(--foreground-strong)]">{project.name}</div>
                  <div className="mt-1 text-sm text-[var(--foreground-muted)]">{project.projectId}</div>
                  <div className="mt-1 text-sm text-[var(--foreground-muted)]">
                    {project.fileCount} files · {counts.ready} ready · {counts.active} active · {counts.failed} failed
                  </div>
                  <div className="mt-1 text-sm text-[var(--foreground-muted)]">{formatDate(project.updatedAt)}</div>
                </Link>
              );
            })}
          </div>
        )}
      </Card>

      <Card title="Needs Attention">
        {activeProjects.length === 0 && blockedProjects.length === 0 ? (
          <EmptyState description="There are no active or blocked projects." title="Queue clear" />
        ) : (
          <div className="space-y-3">
            {[...activeProjects, ...blockedProjects.filter((project) => !activeProjects.includes(project))]
              .slice(0, 8)
              .map((project) => {
                const counts = projectStatusCounts(project);
                return (
                  <Link
                    className="block rounded-[12px] border border-[#eee] p-4 transition-colors hover:bg-[var(--background-muted)]"
                    href={`/projects/${encodeURIComponent(project.projectId)}`}
                    key={project.projectId}
                  >
                    <div className="text-sm font-semibold text-[var(--foreground-strong)]">{project.name}</div>
                    <div className="mt-1 text-sm text-[var(--foreground-muted)]">
                      {counts.active} active · {counts.failed} failed · {project.fileCount} files
                    </div>
                  </Link>
                );
              })}
          </div>
        )}
      </Card>
    </div>
  );
}
