"use client";

import { useCallback, useEffect, useState } from "react";
import { UploadDrop } from "@/components/upload/UploadDrop";
import { listFiles, FileItem, createShare } from "@/services/api";
import { clsx } from "clsx";
import Link from "next/link";

const STATUS_MAP: Record<string, { label: string; bg: string; text: string }> = {
  ready:      { label: "READY",      bg: "bg-emerald-500/10",   text: "text-emerald-500" },
  processing: { label: "PROCESSING",  bg: "bg-blue-500/10",        text: "text-blue-400" },
  running:    { label: "RUNNING",  bg: "bg-blue-500/10",        text: "text-blue-400" },
  queued:     { label: "QUEUED",   bg: "bg-amber-500/10",     text: "text-amber-500" },
  failed:     { label: "FAILED",       bg: "bg-red-500/10",       text: "text-red-500" },
};

function StatusBadge({ status }: { status: string }) {
  const s = (status || "").toLowerCase();
  const config = STATUS_MAP[s] || { label: status.toUpperCase(), bg: "bg-gray-800", text: "text-gray-400" };
  return (
    <span className={clsx("inline-flex items-center rounded px-2 py-0.5 text-[9px] font-bold tracking-widest", config.bg, config.text)}>
      {config.label}
    </span>
  );
}

function SummaryCard({ title, value, sub, icon }: { title: string; value: string | number; sub?: string; icon?: string }) {
  return (
    <div className="bg-[#2d2d2d] border border-gray-800 p-5 rounded-xl shadow-sm">
      <div className="flex justify-between items-start mb-2">
        <span className="text-[10px] font-bold uppercase tracking-widest text-gray-500">{title}</span>
        <span className="text-lg opacity-50">{icon}</span>
      </div>
      <div className="text-2xl font-bold text-white">{value}</div>
      {sub && <div className="text-[11px] text-gray-500 mt-1">{sub}</div>}
    </div>
  );
}

export default function DashboardPage() {
  const [files, setFiles] = useState<FileItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    try {
      const data = await listFiles();
      setFiles(data);
      setError(null);
    } catch (e: any) {
      setError(e?.message || "Failed to load workspace data.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
    const id = setInterval(load, 15000);
    return () => clearInterval(id);
  }, [load]);

  const stats = {
    totalFiles: files.length,
    activeJobs: files.filter(f => ['queued', 'processing', 'running'].includes(f.status.toLowerCase())).length,
    storage: (files.reduce((acc, f) => acc + (f.size_bytes || 0), 0) / (1024 * 1024)).toFixed(1) + " MB",
    plan: "Pro (Beta)"
  };

  return (
    <div className="max-w-6xl mx-auto space-y-8 p-6 lg:p-10 text-gray-100">
      <header>
        <h1 className="text-3xl font-bold tracking-tight text-white">Workspace <span className="text-blue-500">Overview</span></h1>
        <p className="text-gray-400 mt-1">Manage your engineering assets and active processing pipeline.</p>
      </header>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <SummaryCard title="Total Assets" value={stats.totalFiles} icon="📂" />
        <SummaryCard title="Active Pipeline" value={stats.activeJobs} sub={stats.activeJobs > 0 ? "Jobs in progress" : "Queue empty"} icon="⚙️" />
        <SummaryCard title="Cloud Storage" value={stats.storage} sub="Used of 10 GB" icon="☁️" />
        <SummaryCard title="Current Plan" value={stats.plan} sub="Admin access active" icon="🛡️" />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Left Column: Upload */}
        <div className="lg:col-span-1 space-y-6">
          <section className="bg-[#2d2d2d] border border-gray-800 rounded-xl p-6 shadow-xl">
            <h2 className="text-sm font-bold uppercase tracking-widest text-gray-400 mb-4">Quick Upload</h2>
            <UploadDrop onUploaded={load} />
            <p className="text-[10px] text-gray-500 mt-4 text-center">
              Supported: STEP, STL, DXF, PDF (Max 100MB)
            </p>
          </section>
        </div>

        {/* Right Column: Recent Files */}
        <div className="lg:col-span-2 space-y-4">
          <div className="flex items-center justify-between px-2">
            <h2 className="text-sm font-bold uppercase tracking-widest text-gray-400">Recent Activity</h2>
            <button onClick={load} className={clsx("text-xs text-blue-500 hover:underline", loading && "animate-pulse")}>
              {loading ? "Syncing..." : "Refresh"}
            </button>
          </div>

          {error ? (
            <div className="bg-red-900/20 border border-red-900/50 p-4 rounded-xl text-red-400 text-sm">
              {error}
            </div>
          ) : files.length === 0 ? (
            <div className="bg-[#2d2d2d]/50 border border-dashed border-gray-800 rounded-xl py-20 text-center">
              <p className="text-gray-500 text-sm">No files found in this workspace.</p>
            </div>
          ) : (
            <div className="space-y-2">
              {files.slice(0, 8).map((file) => (
                <div key={file.file_id} className="group bg-[#2d2d2d] hover:bg-[#363636] border border-gray-800 p-3 rounded-lg flex items-center gap-4 transition-all">
                  <div className="w-10 h-10 bg-black/20 rounded flex items-center justify-center text-lg">
                    {file.kind === '3d' ? '⚙️' : '📄'}
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                      <span className="truncate text-sm font-medium text-white">{file.original_name}</span>
                      <StatusBadge status={file.status} />
                    </div>
                    <div className="text-[10px] text-gray-500 font-mono">#{file.file_id.slice(0,8)}</div>
                  </div>
                  <div className="flex items-center gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
                    <Link href={`/console?file=${file.file_id}`} className="bg-blue-600 hover:bg-blue-500 text-white text-[10px] font-bold px-3 py-1.5 rounded uppercase">
                      Open
                    </Link>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
