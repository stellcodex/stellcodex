"use client";

import { useCallback, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { UploadDrop } from "@/components/upload/UploadDrop";
import { createShare, listRecentFiles, RecentFileItem } from "@/services/api";

const STATUS_LABEL: Record<string, { text: string; color: string }> = {
  ready:      { text: "Hazır",      color: "#16a34a" },
  processing: { text: "İşleniyor", color: "#0284c7" },
  running:    { text: "İşleniyor", color: "#0284c7" },
  queued:     { text: "Kuyrukta",   color: "#9333ea" },
  pending:    { text: "Bekliyor",   color: "#d97706" },
  failed:     { text: "Hata",       color: "#dc2626" },
};

function statusStyle(raw: string) {
  const s = (raw || "").toLowerCase();
  return STATUS_LABEL[s] || { text: raw, color: "#6b7280" };
}

function timeAgo(iso: string) {
  if (!iso) return "";
  const diff = Date.now() - new Date(iso).getTime();
  const m = Math.floor(diff / 60000);
  if (m < 1) return "Az önce";
  if (m < 60) return `${m} dk önce`;
  const h = Math.floor(m / 60);
  if (h < 24) return `${h} sa önce`;
  return `${Math.floor(h / 24)} gün önce`;
}

export default function DashboardPage() {
  const router = useRouter();
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
    const id = setInterval(() => void load(), 8000);
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
    <div className="flex h-full flex-col gap-6 p-6">
      {/* Upload alanı */}
      <section>
        <h1 className="mb-3 text-lg font-semibold text-slate-900">Dosya Yükle</h1>
        <div className="rounded-2xl border border-slate-200 bg-white p-4">
          <UploadDrop onUploaded={() => void load()} />
        </div>
      </section>

      {/* Son dosyalar */}
      <section className="flex-1 min-h-0">
        <div className="mb-3 flex items-center justify-between">
          <h2 className="text-base font-semibold text-slate-900">Son Yüklenenler</h2>
          <button
            onClick={() => void load()}
            className="text-xs text-slate-500 hover:text-slate-900 transition"
          >
            Yenile
          </button>
        </div>

        {loading && (
          <div className="text-sm text-slate-500">Yükleniyor...</div>
        )}
        {!loading && error && (
          <div className="text-sm text-red-600">{error}</div>
        )}
        {!loading && !error && recent.length === 0 && (
          <div className="rounded-2xl border border-dashed border-slate-200 bg-slate-50 p-8 text-center">
            <div className="text-3xl">⭘</div>
            <div className="mt-2 text-sm text-slate-500">Henüz dosya yok. Yukarıdan yükleyin.</div>
          </div>
        )}

        {!loading && recent.length > 0 && (
          <div className="grid gap-2">
            {recent.map((file) => {
              const st = statusStyle(file.status);
              const isReady = file.status === "ready";
              const link = shareLinks[file.file_id];
              return (
                <div
                  key={file.file_id}
                  className="flex items-center gap-3 rounded-xl border border-slate-100 bg-white px-4 py-3 hover:border-slate-300 transition"
                >
                  {/* Thumbnail */}
                  <div className="h-10 w-10 shrink-0 overflow-hidden rounded-lg border border-slate-100 bg-slate-50">
                    {file.thumbnail_url ? (
                      // eslint-disable-next-line @next/next/no-img-element
                      <img
                        src={file.thumbnail_url}
                        alt={file.original_name}
                        className="h-full w-full object-cover"
                      />
                    ) : (
                      <div className="flex h-full w-full items-center justify-center text-lg text-slate-300">
                        {file.kind === "3d" ? "⬢" : file.kind === "2d" ? "⬜" : "⬡"}
                      </div>
                    )}
                  </div>

                  {/* İsim + durum */}
                  <div className="min-w-0 flex-1">
                    <div className="truncate text-sm font-medium text-slate-900" title={file.original_name}>
                      {file.original_name}
                    </div>
                    <div className="mt-0.5 flex items-center gap-2 text-xs text-slate-400">
                      <span style={{ color: st.color }} className="font-semibold">
                        {st.text}
                      </span>
                      <span>·</span>
                      <span>{timeAgo(file.created_at)}</span>
                    </div>
                  </div>

                  {/* Aksiyonlar */}
                  <div className="flex shrink-0 items-center gap-2">
                    {isReady && (
                      <button
                        onClick={() => router.push(`/view/${file.file_id}`)}
                        className="rounded-lg bg-slate-900 px-3 py-1.5 text-xs font-semibold text-white hover:bg-slate-700 transition"
                      >
                        Aç
                      </button>
                    )}
                    {isReady && (
                      <button
                        onClick={() => void handleShare(file.file_id)}
                        className="rounded-lg border border-slate-200 px-3 py-1.5 text-xs font-semibold text-slate-600 hover:bg-slate-50 transition"
                        title={link ? "Kopyalandı! Tekrar tıkla" : "Paylaşım linki oluştur ve kopyala"}
                      >
                        {sharing === file.file_id ? "..." : link ? "✓ Kopyala" : "Paylaş"}
                      </button>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </section>
    </div>
  );
}
