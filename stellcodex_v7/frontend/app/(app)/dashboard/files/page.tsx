"use client";

import { useEffect, useState } from "react";
import { SectionHeader } from "@/components/layout/SectionHeader";
import { EmptyState, ErrorState, LoadingState } from "@/components/ui/StateBlocks";
import { FileItem, listFiles } from "@/services/api";

function formatBytes(bytes: number) {
  if (!Number.isFinite(bytes)) return "-";
  if (bytes < 1024) return `${bytes} B`;
  const units = ["KB", "MB", "GB"];
  let val = bytes / 1024;
  let idx = 0;
  while (val >= 1024 && idx < units.length - 1) {
    val /= 1024;
    idx += 1;
  }
  return `${val.toFixed(1)} ${units[idx]}`;
}

export default function DashboardFilesPage() {
  const [items, setItems] = useState<FileItem[]>([]);
  const [state, setState] = useState<"loading" | "ready" | "error">("loading");
  const [error, setError] = useState<string | null>(null);
  const [search, setSearch] = useState("");
  const [filterFormat, setFilterFormat] = useState("");
  const [filterStatus, setFilterStatus] = useState("");

  useEffect(() => {
    let mounted = true;
    listFiles()
      .then((data) => {
        if (!mounted) return;
        setItems(data);
        setState("ready");
      })
      .catch((err) => {
        if (!mounted) return;
        setError(err?.message || "Files could not be loaded.");
        setState("error");
      });
    return () => {
      mounted = false;
    };
  }, []);

  const formats = Array.from(new Set(items.map((i) => i.content_type).filter(Boolean)));
  const statuses = Array.from(new Set(items.map((i) => i.status).filter(Boolean)));

  const filtered = items.filter((item) => {
    if (search && !item.original_filename.toLowerCase().includes(search.toLowerCase())) return false;
    if (filterFormat && item.content_type !== filterFormat) return false;
    if (filterStatus && item.status !== filterStatus) return false;
    return true;
  });

  return (
    <div className="space-y-6">
      <SectionHeader
        title="My File Library"
        description="Search, filter, and manage your files."
        crumbs={[
          { label: "Dashboard", href: "/dashboard" },
          { label: "Files" },
        ]}
      />

      <div className="rounded-2xl border border-slate-200 bg-white p-5">
        <div className="flex flex-wrap items-center gap-3">
          <input
            className="flex-1 rounded-xl border border-slate-200 px-3 py-2 text-sm"
            placeholder="Search"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
          <select
            className="rounded-xl border border-slate-200 px-3 py-2 text-sm"
            value={filterFormat}
            onChange={(e) => setFilterFormat(e.target.value)}
          >
            <option value="">All formats</option>
            {formats.map((f) => <option key={f} value={f}>{f}</option>)}
          </select>
          <select
            className="rounded-xl border border-slate-200 px-3 py-2 text-sm"
            value={filterStatus}
            onChange={(e) => setFilterStatus(e.target.value)}
          >
            <option value="">All statuses</option>
            {statuses.map((s) => <option key={s} value={s}>{s}</option>)}
          </select>
        </div>

        <div className="mt-5">
          {state === "loading" ? <LoadingState lines={6} /> : null}
          {state === "error" ? (
            <ErrorState title="Could not load" description={error || ""} />
          ) : null}
          {state === "ready" && filtered.length === 0 ? (
            <EmptyState title="No files yet" description="Upload a file to see it here." />
          ) : null}
          {state === "ready" && filtered.length > 0 ? (
            <div className="grid gap-3">
              {filtered.map((item) => (
                <div
                  key={item.file_id}
                  className="flex flex-col gap-2 rounded-xl border border-slate-100 bg-slate-50 px-4 py-3 sm:flex-row sm:items-center sm:justify-between"
                >
                  <div>
                    <div className="text-sm font-semibold text-slate-900">
                      {item.original_filename}
                    </div>
                    <div className="text-xs text-slate-500">
                      {item.status} · {formatBytes(item.size_bytes)}
                    </div>
                  </div>
                  <div className="text-xs text-slate-500">{item.content_type}</div>
                </div>
              ))}
            </div>
          ) : null}
        </div>
      </div>
    </div>
  );
}
