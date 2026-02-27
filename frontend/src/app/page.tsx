"use client";

import Image from "next/image";
import Link from "next/link";
import { useCallback, useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import logo from "@/app/gorsel/logo.png";
import { UploadDrop } from "@/components/upload/UploadDrop";
import { createShare, getFile, listRecentFiles, type RecentFileItem } from "@/services/api";

type StatusTone = {
  bg: string;
  text: string;
  border: string;
  label: string;
};

function normalizeStatus(raw: string) {
  const status = (raw || "").toLowerCase();
  if (status === "ready" || status === "succeeded") return "ready";
  if (status === "failed") return "failed";
  if (status === "running" || status === "processing") return "running";
  return "queued";
}

function statusTone(status: string): StatusTone {
  const normalized = normalizeStatus(status);
  if (normalized === "ready") {
    return { bg: "#e8f1ff", text: "#1d4ed8", border: "#c7ddff", label: "READY" };
  }
  if (normalized === "running") {
    return { bg: "#eef6f5", text: "#0f766e", border: "#bfe2df", label: "PROCESSING" };
  }
  if (normalized === "failed") {
    return { bg: "#fff1f2", text: "#b91c1c", border: "#fecdd3", label: "FAILED" };
  }
  return { bg: "#f7f5ef", text: "#4f6f6b", border: "#d7d3c8", label: "QUEUED" };
}

function formatWhen(value: string) {
  if (!value) return "-";
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) return "-";
  return parsed.toLocaleString("tr-TR", {
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  });
}

export default function HomePage() {
  const router = useRouter();
  const [recent, setRecent] = useState<RecentFileItem[]>([]);
  const [selected, setSelected] = useState<RecentFileItem | null>(null);
  const [loadingRecent, setLoadingRecent] = useState(true);
  const [recentError, setRecentError] = useState<string | null>(null);
  const [shareBusy, setShareBusy] = useState(false);
  const [shareError, setShareError] = useState<string | null>(null);
  const [shareLink, setShareLink] = useState<string | null>(null);

  const refreshRecent = useCallback(async () => {
    setLoadingRecent(true);
    setRecentError(null);
    try {
      const files = await listRecentFiles(20);
      setRecent(files);
      setSelected((current) => {
        if (!current) return files[0] ?? null;
        const synced = files.find((item) => item.file_id === current.file_id);
        return synced || current;
      });
    } catch (error) {
      setRecentError(error instanceof Error ? error.message : "Son yüklenenler alınamadı.");
    } finally {
      setLoadingRecent(false);
    }
  }, []);

  useEffect(() => {
    void refreshRecent();
  }, [refreshRecent]);

  const selectedStatus = selected ? normalizeStatus(selected.status) : "queued";
  const viewerReady = selectedStatus === "ready";
  const selectedTone = statusTone(selected?.status || "queued");

  useEffect(() => {
    if (!selected?.file_id) return;
    if (selectedStatus === "ready" || selectedStatus === "failed") return;

    let cancelled = false;
    const tick = async () => {
      try {
        const file = await getFile(selected.file_id);
        if (cancelled) return;
        const next: RecentFileItem = {
          file_id: file.file_id,
          original_name: file.original_name,
          kind: file.kind,
          status: file.status,
          created_at: file.created_at,
          thumbnail_url: file.thumbnail_url || null,
        };
        setSelected((current) => (current && current.file_id === next.file_id ? next : current));
        setRecent((current) => current.map((item) => (item.file_id === next.file_id ? { ...item, ...next } : item)));
      } catch {
        // keep existing state; next poll will retry.
      }
    };

    const intervalId = window.setInterval(() => {
      void tick();
    }, 2000);
    void tick();
    return () => {
      cancelled = true;
      window.clearInterval(intervalId);
    };
  }, [selected?.file_id, selectedStatus]);

  const handleCreateShare = useCallback(async () => {
    if (!selected || !viewerReady) return;
    setShareBusy(true);
    setShareError(null);
    try {
      const result = await createShare(selected.file_id);
      setShareLink(`${window.location.origin}/share/${result.token}`);
    } catch (error) {
      setShareError(error instanceof Error ? error.message : "Paylaşım linki oluşturulamadı.");
    } finally {
      setShareBusy(false);
    }
  }, [selected, viewerReady]);

  const selectedInfo = useMemo(() => {
    if (!selected) return null;
    return [
      { label: "Dosya", value: selected.original_name },
      { label: "Kimlik", value: selected.file_id },
      { label: "Tür", value: selected.kind.toUpperCase() },
      { label: "Yüklendi", value: formatWhen(selected.created_at) },
    ];
  }, [selected]);

  return (
    <div className="min-h-[100dvh] bg-[#f5f5f4] text-[#111827]">
      <header className="sticky top-0 z-20 border-b border-[#e7e5e4] bg-white/95 backdrop-blur">
        <div className="mx-auto flex h-16 max-w-[1280px] items-center justify-between gap-3 px-4 sm:px-6">
          <Link href="/" className="flex items-center gap-2">
            <Image src={logo} alt="STELLCODEX logo" width={34} height={34} className="h-8 w-8 rounded-md object-cover" />
            <span className="text-sm font-semibold tracking-wide">STELLCODEX</span>
          </Link>
          <div className="flex items-center gap-2">
            <span className="rounded-full border border-[#d6d3d1] bg-[#fafaf9] px-2.5 py-1 text-[11px] font-semibold uppercase tracking-[0.12em] text-[#57534e]">
              Guest
            </span>
            <Link href="/upload" className="rounded-lg border border-[#111827] bg-[#111827] px-3 py-2 text-xs font-semibold text-white">
              Dosya Yükle
            </Link>
          </div>
        </div>
      </header>

      <main className="mx-auto max-w-[1280px] px-4 py-5 sm:px-6 sm:py-6">
        <div className="grid grid-cols-1 gap-4 lg:grid-cols-[1.2fr_0.8fr]">
          <section className="order-2 rounded-2xl border border-[#e7e5e4] bg-white p-4 lg:order-1">
            <div className="mb-3 flex items-center justify-between gap-2">
              <h2 className="text-sm font-semibold text-[#111827]">Son Yüklenenler</h2>
              <button
                type="button"
                onClick={() => void refreshRecent()}
                className="rounded-lg border border-[#d6d3d1] bg-[#fafaf9] px-3 py-1.5 text-xs font-semibold text-[#44403c]"
              >
                Yenile
              </button>
            </div>

            {loadingRecent ? <div className="text-sm text-[#6b7280]">Liste yükleniyor...</div> : null}
            {!loadingRecent && recentError ? <div className="text-sm text-red-600">{recentError}</div> : null}
            {!loadingRecent && !recentError && recent.length === 0 ? (
              <div className="rounded-xl border border-dashed border-[#d6d3d1] bg-[#fafaf9] p-4 text-sm text-[#57534e]">
                Henüz dosya yok. Sağdan yükleyin.
              </div>
            ) : null}

            {!loadingRecent && !recentError && recent.length > 0 ? (
              <div className="grid gap-2">
                {recent.map((file) => {
                  const tone = statusTone(file.status);
                  const isSelected = selected?.file_id === file.file_id;
                  return (
                    <div
                      key={file.file_id}
                      className={`grid grid-cols-[1fr_auto_auto] items-center gap-2 rounded-xl border px-3 py-2 ${
                        isSelected ? "border-[#111827] bg-[#f8fafc]" : "border-[#e7e5e4] bg-white"
                      }`}
                    >
                      <button
                        type="button"
                        onClick={() => {
                          setSelected(file);
                          setShareLink(null);
                          setShareError(null);
                        }}
                        className="truncate text-left text-sm text-[#1f2937]"
                        title={file.original_name}
                      >
                        {file.original_name}
                      </button>
                      <span
                        className="rounded-full px-2.5 py-1 text-[10px] font-bold tracking-[0.1em]"
                        style={{ background: tone.bg, color: tone.text, border: `1px solid ${tone.border}` }}
                      >
                        {tone.label}
                      </span>
                      <button
                        type="button"
                        onClick={() => router.push(`/view/${file.file_id}`)}
                        className="rounded-lg border border-[#111827] px-3 py-1.5 text-xs font-semibold text-[#111827]"
                      >
                        Aç
                      </button>
                    </div>
                  );
                })}
              </div>
            ) : null}
          </section>

          <section className="order-1 grid gap-4 lg:order-2">
            <div className="rounded-2xl border border-[#e7e5e4] bg-white p-4">
              <h2 className="mb-3 text-sm font-semibold text-[#111827]">Dosya Yükle</h2>
              <UploadDrop />
            </div>

            <div className="rounded-2xl border border-[#e7e5e4] bg-white p-4">
              <h2 className="mb-3 text-sm font-semibold text-[#111827]">Seçili Dosya Detayı</h2>
              {!selected || !selectedInfo ? (
                <div className="rounded-xl border border-dashed border-[#d6d3d1] bg-[#fafaf9] p-4 text-sm text-[#57534e]">
                  Soldan bir dosya seçin veya yeni dosya yükleyin.
                </div>
              ) : (
                <div className="grid gap-3">
                  <div className="flex items-center justify-between gap-2">
                    <div className="truncate text-sm font-semibold text-[#111827]" title={selected.original_name}>
                      {selected.original_name}
                    </div>
                    <span
                      className="rounded-full px-2.5 py-1 text-[10px] font-bold tracking-[0.1em]"
                      style={{ background: selectedTone.bg, color: selectedTone.text, border: `1px solid ${selectedTone.border}` }}
                    >
                      {selectedTone.label}
                    </span>
                  </div>

                  <div className="grid gap-2 rounded-xl border border-[#e7e5e4] bg-[#fafaf9] p-3">
                    {selectedInfo.map((row) => (
                      <div key={row.label} className="grid grid-cols-[84px_1fr] gap-2 text-xs">
                        <div className="font-semibold uppercase tracking-[0.08em] text-[#6b7280]">{row.label}</div>
                        <div className="truncate text-[#1f2937]" title={row.value}>
                          {row.value}
                        </div>
                      </div>
                    ))}
                  </div>

                  <div className="grid gap-2">
                    <button
                      type="button"
                      disabled={!viewerReady}
                      onClick={() => selected && router.push(`/view/${selected.file_id}`)}
                      className={`rounded-lg px-3 py-2 text-sm font-semibold ${
                        viewerReady
                          ? "border border-[#111827] bg-[#111827] text-white"
                          : "cursor-not-allowed border border-[#d6d3d1] bg-[#f5f5f4] text-[#a8a29e]"
                      }`}
                    >
                      Viewer&apos;a git
                    </button>

                    <button
                      type="button"
                      disabled={!viewerReady || shareBusy}
                      onClick={() => void handleCreateShare()}
                      className={`rounded-lg px-3 py-2 text-sm font-semibold ${
                        viewerReady
                          ? "border border-[#0f766e] bg-[#0f766e] text-white"
                          : "cursor-not-allowed border border-[#d6d3d1] bg-[#f5f5f4] text-[#a8a29e]"
                      }`}
                    >
                      {shareBusy ? "Paylaşım oluşturuluyor..." : "Paylaş linki oluştur"}
                    </button>

                    {shareLink ? (
                      <div className="grid gap-2 rounded-xl border border-[#d6d3d1] bg-[#fafaf9] p-3 text-xs">
                        <div className="truncate text-[#374151]" title={shareLink}>
                          {shareLink}
                        </div>
                        <button
                          type="button"
                          onClick={async () => {
                            await navigator.clipboard.writeText(shareLink);
                          }}
                          className="w-fit rounded-lg border border-[#d6d3d1] bg-white px-3 py-1.5 text-xs font-semibold text-[#374151]"
                        >
                          Linki kopyala
                        </button>
                      </div>
                    ) : null}
                    {shareError ? <div className="text-xs text-red-600">{shareError}</div> : null}
                    {!viewerReady ? <div className="text-xs text-[#6b7280]">Viewer ve paylaşım, durum READY olduğunda aktif olur.</div> : null}
                  </div>
                </div>
              )}
            </div>
          </section>
        </div>
      </main>
    </div>
  );
}
