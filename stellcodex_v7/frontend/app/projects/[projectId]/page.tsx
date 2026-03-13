"use client";

import { useParams } from "next/navigation";
import { AppShell } from "@/components/shell/AppShell";
import { ErrorState } from "@/components/primitives/ErrorState";
import { LoadingSkeleton } from "@/components/primitives/LoadingSkeleton";
import { ProjectActivityPanel } from "@/components/projects/ProjectActivityPanel";
import { ProjectFilesTable } from "@/components/projects/ProjectFilesTable";
import { ProjectHeader } from "@/components/projects/ProjectHeader";
import { ProjectSummaryPanel } from "@/components/projects/ProjectSummaryPanel";
import { ProjectWorkflowSummaryPanel } from "@/components/projects/ProjectWorkflowSummaryPanel";
import { useProjectDetail } from "@/lib/hooks/useProjectDetail";

export default function ProjectDetailPage() {
  const params = useParams<{ projectId: string }>();
  const projectId = params.projectId;
  const { data, loading, error, refresh } = useProjectDetail(projectId);

  return (
    <AppShell
      title="Project detail"
      subtitle="Files, activity, and workflow summary"
      breadcrumbs={[
        { href: "/projects", label: "Projects" },
        { label: data?.name || projectId },
      ]}
    >
      {loading ? <LoadingSkeleton label="Loading project detail" /> : null}
      {error ? <ErrorState title="Project unavailable" description={error} retryLabel="Retry" onRetry={() => void refresh()} /> : null}
      {data ? (
        <div className="sc-stack">
          <ProjectHeader project={data} />
          <div className="sc-grid sc-grid-3">
            <ProjectSummaryPanel project={data} />
            <ProjectWorkflowSummaryPanel project={data} />
            <ProjectActivityPanel files={data.files} />
          </div>
          <ProjectFilesTable files={data.files} />
        </div>
      ) : null}
    </AppShell>
  );
}
