"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useMemo, useState } from "react";
import { ListRow } from "@/components/common/ListRow";
import { Card } from "@/components/ui/Card";
import { tokens } from "@/lib/tokens";
import { applications } from "@/data/applications";
import {
  DEFAULT_PROJECT_ID,
  DEFAULT_PROJECT_NAME,
  formatWorkspaceDate,
  listWorkspaceFilesByProject,
  subscribeWorkspaceUpdates,
  type WorkspaceFileRecord,
} from "@/lib/workspace-store";

function appHrefForFile(file: WorkspaceFileRecord) {
  if (file.mode === "2d") {
    return `/app/2d?file=${encodeURIComponent(file.fileId)}&project=${encodeURIComponent(file.projectId)}`;
  }
  return `/app/3d?file=${encodeURIComponent(file.fileId)}&project=${encodeURIComponent(file.projectId)}`;
}

export function ProjectWorkspace() {
  const params = useParams();
  const projectId = typeof params.id === "string" && params.id.trim().length > 0 ? params.id : DEFAULT_PROJECT_ID;
  const [files, setFiles] = useState<WorkspaceFileRecord[]>([]);

  useEffect(() => {
    const refresh = () => setFiles(listWorkspaceFilesByProject(projectId));
    refresh();
    return subscribeWorkspaceUpdates(refresh);
  }, [projectId]);

  const projectName = useMemo(() => files[0]?.projectName || DEFAULT_PROJECT_NAME, [files]);

  return (
    <div className="flex flex-col gap-sectionGap">
      <div style={tokens.typography.h2} className="text-[#0c2a2a]">
        Çalışma alanı: {projectName}
      </div>

      {!files.length ? (
        <div className="rounded-r1 border-soft bg-surface px-cardPad py-cardPad text-fs0 text-muted">
          Bu projede henüz dosya yok. <Link href="/upload" className="underline">Dosya yükleyin</Link>.
        </div>
      ) : (
        <div className="flex flex-col gap-3">
          {files.map((file) => (
            <ListRow
              key={file.fileId}
              title={file.originalFilename}
              subtitle={`Yüklendi: ${formatWorkspaceDate(file.uploadedAt)}`}
              href={appHrefForFile(file)}
              trailing={file.mode === "2d" ? "2D" : "3D"}
            />
          ))}
        </div>
      )}

      <div style={tokens.typography.h2} className="text-[#0c2a2a]">
        Uygulamalar
      </div>
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        {applications.map((app) => (
          <Link key={app.href} href={app.href} className="block">
            <Card hover className="p-4">
              <div className="flex items-center gap-3">
                <span className="text-xl">{app.icon}</span>
                <div style={tokens.typography.h2} className="text-[#0c2a2a]">
                  {app.label}
                </div>
              </div>
              <div style={tokens.typography.body} className="mt-2 text-[#4f6f6b]">
                {app.description}
              </div>
            </Card>
          </Link>
        ))}
      </div>
    </div>
  );
}
