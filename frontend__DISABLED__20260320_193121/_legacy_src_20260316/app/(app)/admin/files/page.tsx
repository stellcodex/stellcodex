"use client";

import { useEffect, useState } from "react";
import { SectionHeader } from "@/components/layout/SectionHeader";
import { EmptyState } from "@/components/ui/StateBlocks";
import { fetchAdminFiles } from "@/services/admin";

type FileItem = {
  file_id: string;
  original_filename: string;
  status: string;
  visibility: string;
  privacy: string;
  owner_user_id?: string | null;
  owner_anon_sub?: string | null;
  created_at?: string;
};

export default function AdminFilesPage() {
  const [files, setFiles] = useState<FileItem[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let active = true;
    fetchAdminFiles()
      .then((data) => {
        if (!active) return;
        setFiles(data.items || []);
      })
      .catch((e: any) => {
        if (!active) return;
        setError(e?.message || "Files could not be loaded.");
      });
    return () => {
      active = false;
    };
  }, []);

  return (
    <div className="space-y-6">
      <SectionHeader
        title="Files"
        description="Visibility and archive controls."
        crumbs={[{ label: "Admin", href: "/admin" }, { label: "Files" }]}
      />
      {error ? (
        <EmptyState title="No file data" description={error} />
      ) : (
        <div className="rounded-2xl border border-slate-200 bg-white p-5">
          <div className="text-sm font-semibold text-slate-900">Recent files</div>
          <div className="mt-3 space-y-2 text-sm text-slate-700">
            {files.length ? (
              files.map((f) => (
                <div key={f.file_id} className="rounded-lg border border-slate-100 p-2">
                  <div className="font-medium">{f.original_filename}</div>
                  <div className="text-xs text-slate-500">
                    {f.file_id} · {f.status} · {f.privacy} · {f.visibility}
                  </div>
                </div>
              ))
            ) : (
              <div className="text-sm text-slate-500">No files are available.</div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
