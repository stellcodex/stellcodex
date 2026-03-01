"use client";

import { useCallback, useEffect, useState } from "react";
// eslint-disable-next-line @typescript-eslint/no-unused-vars
import { useRouter } from "next/navigation";
import { UploadDrop } from "@/components/upload/UploadDrop";
import { createShare, listRecentFiles, RecentFileItem } from "@/services/api";
import { clsx } from "clsx";

const STATUS_MAP: Record<string, { label: string; bg: string; text: string }> = {
  ready:      { label: "Hazır",      bg: "bg-emerald-500/10",   text: "text-emerald-500" },
  processing: { label: "İşleniyor",  bg: "bg-accent/10",        text: "text-accent" },
  running:    { label: "İşleniyor",  bg: "bg-accent/10",        text: "text-accent" },
  queued:     { label: "Kuyrukta",   bg: "bg-amber-500/10",     text: "text-amber-500" },
  pending:    { label: "Bekliyor",   bg: "bg-slate-500/10",     text: "text-slate-400" },
  failed:     { label: "Hata",       bg: "bg-red-500/10",       text: "text-red-500" },
};

function StatusBadge({ status }: { status: string }) {
  const s = (status || "").toLowerCase();
  const config = STATUS_MAP[s] || { label: status, bg: "bg-surface-2", text: "text-muted" };
  
  return (
    <span className={clsx("inline-flex items-center rounded-full px-2 py-0.5 text-[10px] font-bold uppercase tracking-wider", config.bg, config.text)}>
      {config.label}
    </span>
  );
}

function timeAgo(iso: string) {
  if (!iso) return "";
  const diff = Date.now() - new Date(iso).getTime();
  const m = Math.floor(diff / 60000);
  if (m < 1) return "Az önce";
  if (m < 60) return `${m}dk`;
  const h = Math.floor(m / 60);
  if (h < 24) return `${h}sa`;
  return `${Math.floor(h / 24)}g`;
}

export default function DashboardPage() {
  const [recent, setRecent] = useState<RecentFileItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [sharing, setSharing] = useState<string | null>(null);
  const [shareLinks, setShareLinks] = useState<Record<string, string>>({});

  const load = useCallback(async () => {
    try {
      const files = await listRecentFiles(20);
      setRecent(files);
      setError(null);
    } catch (e: any) {
      setError(e?.message || "Dosyalar yüklenemedi.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void load();
    const id = setInterval(() => void load(), 10000);
    return () => clearInterval(id);
  }, [load]);

  const handleShare = useCallback(async (fileId: string) => {
    if (shareLinks[fileId]) {
      await navigator.clipboard.writeText(shareLinks[fileId]);
      return;
    }
    setSharing(fileId);
    try {
      const result = await createShare(fileId);
      const link = `${window.location.origin}/s/${result.token}`;
      setShareLinks((prev) => ({ ...prev, [fileId]: link }));
      await navigator.clipboard.writeText(link);
    } catch {
      // ignore
    } finally {
      setSharing(null);
    }
  }, [shareLinks]);

  return (
    <div className="mx-auto max-w-5xl space-y-8 p-6 lg:p-10">
      {/* Header Section */}
      <header className="flex flex-col gap-2">
        <h1 className="text-2xl font-bold tracking-tight text-text">Dashboard</h1>
        <p className="text-sm text-muted">Yeni mühendislik dosyalarını yükleyin veya son çalışmalarınızı yönetin.</p>
      </header>

      {/* Upload Area */}
      <section className="relative overflow-hidden rounded-3xl border border-white/5 bg-surface p-1 shadow-2xl">
         <div className="rounded-[22px] border border-white/5 bg-surface-2/50 p-6 backdrop-blur-sm">
            <UploadDrop onUploaded={() => void load()} />
         </div>
      </section>

      {/* Files Section */}
      <section className="space-y-4">
        <div className="flex items-center justify-between px-2">
          <h2 className="text-lg font-semibold text-text">Son Yüklenenler</h2>
          <button 
            onClick={() => void load()} 
            className="group flex items-center gap-1.5 text-xs font-medium text-muted hover:text-accent transition-colors"
          >
            <span className={clsx("transition-transform group-active:rotate-180", loading && "animate-spin")}>↻</span>
            Yenile
          </button>
        </div>

        {loading && recent.length === 0 ? (
          <div className="grid gap-3">
             {[1, 2, 3].map(i => <div key={i} className="h-16 animate-pulse rounded-2xl bg-surface-2" />)}
          </div>
        ) : error ? (
          <div className="rounded-2xl border border-red-500/10 bg-red-500/5 p-6 text-center text-sm text-red-400">
            {error}
          </div>
        ) : recent.length === 0 ? (
          <div className="flex flex-col items-center justify-center rounded-3xl border border-dashed border-white/10 bg-surface/50 py-16 text-center">
            <div className="mb-4 flex h-16 w-16 items-center justify-center rounded-full bg-surface-2 text-2xl">📁</div>
            <p className="text-sm text-muted">Henüz hiç dosya yüklememişsiniz.</p>
          </div>
        ) : (
          <div className="grid gap-3">
            {recent.map((file) => (
              <div 
                key={file.file_id} 
                className="group flex items-center gap-4 rounded-2xl border border-white/5 bg-surface p-3 transition-all hover:bg-surface-2 hover:shadow-lg"
              >
                {/* File Icon */}
                <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-xl bg-surface-2 text-xl shadow-inner group-hover:bg-accent/10 group-hover:text-accent transition-colors">
                  {file.original_name.toLowerCase().endsWith('.step') || file.original_name.toLowerCase().endsWith('.stp') ? '⚙️' : '📄'}
                </div>

                {/* Info */}
                <div className="min-w-0 flex-1 flex flex-col gap-0.5">
                  <div className="flex items-center gap-2">
                    <span className="truncate text-sm font-semibold text-text group-hover:text-accent transition-colors">
                      {file.original_name}
                    </span>
                    <StatusBadge status={file.status} />
                  </div>
                  <div className="flex items-center gap-2 text-[11px] text-muted-2">
                    <span>#{file.file_id}</span>
                    <span>•</span>
                    <span>{timeAgo(file.created_at)}</span>
                  </div>
                </div>

                {/* Actions */}
                <div className="flex items-center gap-2 pr-2 opacity-0 group-hover:opacity-100 transition-opacity">
                  <button
                    onClick={() => handleShare(file.file_id)}
                    disabled={sharing === file.file_id}
                    className={clsx(
                      "flex h-9 items-center gap-2 rounded-lg px-3 text-xs font-semibold transition-all",
                      shareLinks[file.file_id] 
                        ? "bg-emerald-500 text-white shadow-lg shadow-emerald-500/20" 
                        : "bg-surface-2 text-text hover:bg-accent hover:text-white"
                    )}
                  >
                    {sharing === file.file_id ? '...' : shareLinks[file.file_id] ? 'Kopyalandı ✓' : 'Paylaş'}
                  </button>
                  <a
                    href={`/view/${file.file_id}`}
                    className="flex h-9 w-9 items-center justify-center rounded-lg bg-surface-2 text-text hover:bg-accent hover:text-white transition-all shadow-sm"
                    title="Görüntüle"
                  >
                     👁
                  </a>
                </div>
              </div>
            ))}
          </div>
        )}
      </section>
    </div>
  );
}
