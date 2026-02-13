"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { LayoutShell } from "@/components/layout/LayoutShell";
import { ListRow } from "@/components/common/ListRow";
import { formatWorkspaceDate, listWorkspaceProjects, subscribeWorkspaceUpdates, type WorkspaceProjectSummary } from "@/lib/workspace-store";

export default function MyProjectsPage() {
  const [projects, setProjects] = useState<WorkspaceProjectSummary[]>([]);

  useEffect(() => {
    const refresh = () => setProjects(listWorkspaceProjects());
    refresh();
    return subscribeWorkspaceUpdates(refresh);
  }, []);

  return (
    <LayoutShell>
      <div className="flex flex-col gap-sectionGap">
        <div className="flex items-center justify-between">
          <div className="text-fs2 font-semibold">Projelerim</div>
          <Link href="/upload" className="text-fs0 text-muted">
            Dosya yükle
          </Link>
        </div>
        {!projects.length ? (
          <div className="rounded-r1 border-soft bg-surface px-cardPad py-cardPad text-fs0 text-muted">
            Henüz proje yok.
          </div>
        ) : (
          <div className="flex flex-col gap-cardGap">
            {projects.map((project) => (
              <ListRow
                key={project.projectId}
                title={project.projectName}
                subtitle={`Güncellendi: ${formatWorkspaceDate(project.updatedAt)}`}
                href={`/projects/${project.projectId}`}
                trailing={`${project.fileCount} dosya`}
              />
            ))}
          </div>
        )}
      </div>
    </LayoutShell>
  );
}
